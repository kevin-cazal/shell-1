#!/usr/bin/env python3
"""Split subject/Linux.md into ctfcli challenge folders under challenges/."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBJECT_MD = ROOT / "subject" / "Linux.md"
SUBJECT_IMAGES = ROOT / "subject" / "images"
CHALLENGES = ROOT / "challenges"

# (folder, category, display_name, value, tags, start_heading, end_heading)
# start_heading: first line of section (inclusive). end_heading: first line of next section (exclusive).
# Use None for document start/end.
SECTIONS: list[tuple] = [
    (
        "shell_101/00_intro",
        "shell_101",
        "Shell 101 — Introduction",
        10,
        ["shell_101", "intro"],
        "# Shell 101",
        "## A : Exécution de commandes",
    ),
    (
        "shell_101/a_execution_commandes",
        "shell_101",
        "Shell 101 — Exécution de commandes",
        15,
        ["shell_101", "cal"],
        "## A : Exécution de commandes",
        "## B : Arguments de commande",
    ),
    (
        "shell_101/b_arguments_commande",
        "shell_101",
        "Shell 101 — Arguments de commande",
        15,
        ["shell_101", "arguments"],
        "## B : Arguments de commande",
        "## C : Commandes de base",
    ),
    (
        "shell_101/c01_ls",
        "shell_101",
        "Shell 101 — ls",
        20,
        ["shell_101", "ls"],
        "## C : Commandes de base",
        "### 2. `whoami`",
    ),
    (
        "shell_101/c02_whoami",
        "shell_101",
        "Shell 101 — whoami",
        20,
        ["shell_101", "whoami"],
        "### 2. `whoami`",
        "### 3. `pwd`",
    ),
    (
        "shell_101/c03_pwd",
        "shell_101",
        "Shell 101 — pwd",
        20,
        ["shell_101", "pwd"],
        "### 3. `pwd`",
        "### 4. `cd`",
    ),
    (
        "shell_101/c04_cd",
        "shell_101",
        "Shell 101 — cd",
        20,
        ["shell_101", "cd"],
        "### 4. `cd`",
        "### 5. `mkdir`",
    ),
    (
        "shell_101/c05_mkdir",
        "shell_101",
        "Shell 101 — mkdir",
        20,
        ["shell_101", "mkdir"],
        "### 5. `mkdir`",
        "## D : Copier / Déplacer / Renommer des fichiers",
    ),
    (
        "shell_101/d01_cp",
        "shell_101",
        "Shell 101 — cp",
        20,
        ["shell_101", "cp"],
        "## D : Copier / Déplacer / Renommer des fichiers",
        "### 2 - Déplacer / Renommer : mv",
    ),
    (
        "shell_101/d02_mv",
        "shell_101",
        "Shell 101 — mv",
        20,
        ["shell_101", "mv"],
        "### 2 - Déplacer / Renommer : mv",
        "## E : Créer, éditer, supprimer un fichier",
    ),
    (
        "shell_101/e01_cat",
        "shell_101",
        "Shell 101 — cat",
        20,
        ["shell_101", "cat"],
        "## E : Créer, éditer, supprimer un fichier",
        "### 2 - micro : éditeur de texte",
    ),
    (
        "shell_101/e02_micro",
        "shell_101",
        "Shell 101 — micro",
        20,
        ["shell_101", "micro"],
        "### 2 - micro : éditeur de texte",
        "### 3 - `rm` et `rmdir` : supprimer un fichier / un répertoire",
    ),
    (
        "shell_101/e03_rm",
        "shell_101",
        "Shell 101 — rm et rmdir",
        20,
        ["shell_101", "rm"],
        "### 3 - `rm` et `rmdir` : supprimer un fichier / un répertoire",
        "### Archivage :",
    ),
    (
        "shell_101/e04_archivage",
        "shell_101",
        "Shell 101 — Archivage (tar)",
        15,
        ["shell_101", "tar"],
        "### Archivage :",
        "# Livrable 1",
    ),
    (
        "shell_101/livrable_1",
        "shell_101",
        "Shell 101 — Livrable 1",
        25,
        ["shell_101", "livrable"],
        "# Livrable 1",
        "# Shell 102 : Édition de flux",
    ),
    (
        "shell_102/00_intro",
        "shell_102",
        "Shell 102 — Introduction",
        10,
        ["shell_102", "intro"],
        "# Shell 102 : Édition de flux",
        "## Pipe et redirection",
    ),
    (
        "shell_102/pipe_redirection",
        "shell_102",
        "Shell 102 — Pipe et redirection",
        10,
        ["shell_102", "pipe"],
        "## Pipe et redirection",
        "## Préliminaire : extraire le contenu d'une archive tar",
    ),
    (
        "shell_102/preliminaire_tar",
        "shell_102",
        "Shell 102 — Extraire une archive tar",
        15,
        ["shell_102", "tar"],
        "## Préliminaire : extraire le contenu d'une archive tar",
        "## Préliminaire : un mot sur le format CSV",
    ),
    (
        "shell_102/preliminaire_csv",
        "shell_102",
        "Shell 102 — Format CSV",
        10,
        ["shell_102", "csv"],
        "## Préliminaire : un mot sur le format CSV",
        "### grep",
    ),
    (
        "shell_102/grep_aa7566",
        "shell_102",
        "Shell 102 — grep (vol AA7566)",
        5,
        ["shell_102", "grep"],
        "### grep",
        "#### grep — arrivée 21h42",
    ),
    (
        "shell_102/grep_arrival_942",
        "shell_102",
        "Shell 102 — grep (arrivée 21h42)",
        5,
        ["shell_102", "grep"],
        "#### grep — arrivée 21h42",
        "#### grep — Air France CDG–CAI",
    ),
    (
        "shell_102/grep_af_cdg_cai",
        "shell_102",
        "Shell 102 — grep (Air France CDG–CAI)",
        5,
        ["shell_102", "grep"],
        "#### grep — Air France CDG–CAI",
        "### wc",
    ),
    (
        "shell_102/wc",
        "shell_102",
        "Shell 102 — wc",
        15,
        ["shell_102", "wc"],
        "### wc",
        "### sort",
    ),
    (
        "shell_102/sort",
        "shell_102",
        "Shell 102 — sort",
        15,
        ["shell_102", "sort"],
        "### sort",
        "### head, tail",
    ),
    (
        "shell_102/head_tail",
        "shell_102",
        "Shell 102 — head et tail",
        15,
        ["shell_102", "head", "tail"],
        "### head, tail",
        "### cut",
    ),
    (
        "shell_102/cut",
        "shell_102",
        "Shell 102 — cut",
        15,
        ["shell_102", "cut"],
        "### cut",
        "### uniq",
    ),
    (
        "shell_102/uniq",
        "shell_102",
        "Shell 102 — uniq",
        15,
        ["shell_102", "uniq"],
        "### uniq",
        "### sed",
    ),
    (
        "shell_102/sed",
        "shell_102",
        "Shell 102 — sed",
        15,
        ["shell_102", "sed"],
        "### sed",
        "# Livrable 2:",
    ),
    (
        "shell_102/livrable_2_prerequis",
        "shell_102",
        "Shell 102 — Livrable 2 (prérequis)",
        20,
        ["shell_102", "livrable"],
        "# Livrable 2:",
        "## find et xargs",
    ),
    (
        "shell_102/find_xargs",
        "shell_102",
        "Shell 102 — find et xargs",
        25,
        ["shell_102", "find", "xargs"],
        "## find et xargs",
        "## Grep avancé",
    ),
    (
        "shell_102/grep_avance",
        "shell_102",
        "Shell 102 — Grep avancé",
        25,
        ["shell_102", "grep", "regex"],
        "## Grep avancé",
        None,
    ),
]

# Optional data archives copied from subject/ when present
DATA_ARCHIVES: dict[str, list[str]] = {
    "shell_102/preliminaire_tar": ["data_102.tar"],
    "shell_102/livrable_2_prerequis": ["data_102_delivery.tar"],
}

HINT_RE = re.compile(
    r'<div class="hint">\s*(.*?)\s*</div>',
    re.DOTALL | re.IGNORECASE,
)
SOLUTION_RE = re.compile(
    r'<div\s+hidden\s+class="solution"></div>\s*',
    re.IGNORECASE,
)
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(images/([^)]+)\)(?:\{[^}]*\})?")
PLAIN_HINT_RE = re.compile(r"^Hint:\s*", re.MULTILINE | re.IGNORECASE)


def find_line_index(lines: list[str], heading: str | None) -> int | None:
    if heading is None:
        return None
    target = heading.strip()
    for i, line in enumerate(lines):
        if line.strip() == target:
            return i
    raise ValueError(f"Heading not found: {heading!r}")


def extract_section(lines: list[str], start: str, end: str | None) -> list[str]:
    start_i = find_line_index(lines, start)
    if end is None:
        return lines[start_i:]
    end_i = find_line_index(lines, end)
    return lines[start_i:end_i]


def clean_markdown(text: str) -> str:
    text = SOLUTION_RE.sub("", text)

    def hint_repl(m: re.Match[str]) -> str:
        body = m.group(1).strip()
        body = re.sub(r"^Indice:\s*", "", body, flags=re.IGNORECASE)
        body = re.sub(r"\n\s*\n", "\n", body)
        quoted = "\n".join(f"> {line}" if line else ">" for line in body.splitlines())
        return f"\n> **Indice:**\n{quoted}\n"

    text = HINT_RE.sub(hint_repl, text)

    def plain_hint_repl(m: re.Match[str]) -> str:
        return "> **Indice:**\n"

    text = PLAIN_HINT_RE.sub(plain_hint_repl, text)
    text = re.sub(r"\{width=[^}]+\}", "", text)
    text = IMAGE_RE.sub(r"![\1](\2)", text)
    # Stray closing tag from subject markup (e.g. livrable_1)
    text = re.sub(r"</div>\s*\Z", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def collect_images(text: str) -> list[str]:
    return sorted({m.group(2) for m in IMAGE_RE.finditer(text)})


def needs_quote(s: str) -> bool:
    return bool(re.search(r'[:#\[\]{}&*!|>\'"%@`]', s)) or s.strip() != s


SHELL_101_NAMES: list[str] = [name for folder, _cat, name, *_ in SECTIONS if folder.startswith("shell_101/")]


def write_challenge_yml(
    path: Path,
    name: str,
    category: str,
    description: str,
    value: int,
    tags: list[str],
    files: list[str],
    requirement_names: list[str] | None = None,
) -> None:
    lines = [
        "name: " + (f'"{name}"' if needs_quote(name) else name),
        "author: shell-1",
        f"category: {category}",
        "description: |",
    ]
    for line in description.splitlines():
        lines.append("  " + line if line else "  ")
    lines.extend(
        [
            f"value: {value}",
            "type: standard",
            "state: visible",
        ]
    )
    if requirement_names:
        lines.append("requirements:")
        for req in requirement_names:
            lines.append(f'  - "{req}"')
    lines.append("tags:")
    for tag in tags:
        lines.append(f"  - {tag}")
    if files:
        lines.append("files:")
        for f in files:
            lines.append(f"  - {f}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_images(folder: Path, image_names: list[str]) -> list[str]:
    copied: list[str] = []
    if not image_names or not SUBJECT_IMAGES.is_dir():
        return copied
    for name in image_names:
        src = SUBJECT_IMAGES / name
        if src.is_file():
            shutil.copy2(src, folder / name)
            copied.append(name)
    return copied


def copy_data_archives(folder: Path, rel_folder: str) -> list[str]:
    copied: list[str] = []
    for name in DATA_ARCHIVES.get(rel_folder, []):
        for src_dir in (SUBJECT_IMAGES.parent, folder):
            src = src_dir / name
            if src.is_file():
                dst = folder / name
                if src.resolve() != dst.resolve():
                    shutil.copy2(src, dst)
                copied.append(name)
                break
    return copied


def main() -> None:
    raw = SUBJECT_MD.read_text(encoding="utf-8")
    lines = raw.splitlines(keepends=True)

    prev_name: str | None = None
    for folder, category, name, value, tags, start, end in SECTIONS:
        chunk_lines = extract_section(lines, start, end)
        chunk = "".join(chunk_lines)
        description = clean_markdown(chunk)
        image_names = collect_images(chunk)

        out_dir = CHALLENGES / folder
        out_dir.mkdir(parents=True, exist_ok=True)

        file_list = copy_images(out_dir, image_names)
        file_list.extend(copy_data_archives(out_dir, folder))
        file_list = sorted(set(file_list))

        if folder.startswith("shell_102/"):
            reqs = list(SHELL_101_NAMES)
            if folder != "shell_102/00_intro" and prev_name:
                reqs.append(prev_name)
        elif prev_name:
            reqs = [prev_name]
        else:
            reqs = None

        write_challenge_yml(
            out_dir / "challenge.yml",
            name,
            category,
            description,
            value,
            tags,
            file_list,
            requirement_names=reqs,
        )
        prev_name = name
        print(f"  {folder} ({len(description)} chars, {len(file_list)} files)")

    count = len(list(CHALLENGES.rglob("challenge.yml")))
    print(f"\nWrote {count} challenge.yml files under {CHALLENGES}")


if __name__ == "__main__":
    main()
