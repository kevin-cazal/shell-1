#!/usr/bin/env python3
"""Generate private/flag.txt, private/writeup.md, and flag-format hints in challenge.yml."""

from __future__ import annotations

import csv
import hashlib
import io
import re
import shutil
import subprocess
import tarfile
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CHALLENGES = ROOT / "challenges"
HOME42 = ROOT / "submodules/vm-image/rootfs/home/user42"
ROOTFS = ROOT / "submodules/vm-image/rootfs"
DATA102_GZ = HOME42 / "data_102.tar.gz"
SUBJECT = ROOT / "subject"

FLAG_FOOTER_MARKER = "---\n\n**Drapeau :**"
INTRO_MARKER = "Quelques informations avant de commencer"

INTRO_101 = """\
Bienvenue !

Quelques informations avant de commencer :

1. Les défis sont regroupés en **Shell 101** (fichiers, commandes de base) et **Shell 102** (pipes, texte, find/grep).
2. Chaque étape a un **drapeau** à soumettre dans CTFd pour marquer la progression.
3. Les drapeaux sont au format `shell1{reponse}` (minuscules ; les espaces sont autorisés dans les accolades). Certaines étapes sont des **QCM** : soumettez `shell1{A}` à `shell1{D}` selon la lettre choisie.
4. Travaillez dans le terminal de la VM ; certains livrables vont dans `/mnt/host` ou `answers.txt` comme indiqué dans l'énoncé.

Pour valider cette introduction Shell 101, soumettez : `shell1{pret a commencer}`.

"""

INTRO_102 = """\
Bienvenue dans Shell 102 !

Quelques informations avant de commencer :

1. Les défis sont regroupés en **Shell 101** (fichiers, commandes de base) et **Shell 102** (pipes, texte, find/grep).
2. Chaque étape a un **drapeau** à soumettre dans CTFd pour marquer la progression.
3. Les drapeaux sont au format `shell1{reponse}` (minuscules ; les espaces sont autorisés dans les accolades). Certaines étapes sont des **QCM** : soumettez `shell1{A}` à `shell1{D}` selon la lettre choisie.
4. Travaillez dans le terminal de la VM ; ajoutez vos réponses dans `answers.txt` ou les fichiers demandés.

Pour valider cette introduction Shell 102, soumettez : `shell1{shell 102 start}`.

"""

FLAG_FOOTER = """\

---

**Drapeau :** format `shell1{reponse}`. Dérivez la réponse de l'exercice ci-dessus (commande, nombre, nom de fichier, etc.).
"""

MCQ_FOOTER = """\

---

**Drapeau :** soumettez `shell1{X}` où *X* est la lettre de la bonne réponse (**A**, **B**, **C** ou **D**).
"""


def flag(inner: str) -> str:
    return f"shell1{{{inner.lower()}}}"


def mcq_flag(letter: str) -> str:
    return flag(letter.upper())


def write_flag_files(private: Path, spec: dict[str, Any]) -> str:
    """Write private/flag.txt and/or private/flag.yml. Returns display flag for writeup."""
    flag_def = spec.get("flag_def")
    if flag_def:
        (private / "flag.yml").write_text(
            yaml.safe_dump(flag_def, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        (private / "flag.txt").unlink(missing_ok=True)
        ftype = flag_def.get("type", "static")
        if ftype == "regex":
            return f"regex: {flag_def.get('content', '')}"
        if ftype == "custom":
            return f"custom: {flag_def.get('validator', '')}"
        return str(flag_def.get("content", ""))
    inner = spec["flag"]
    (private / "flag.txt").write_text(inner + "\n", encoding="utf-8")
    (private / "flag.yml").unlink(missing_ok=True)
    return inner


def parse_challenge_yml(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    idx = text.find("description: |")
    if idx < 0:
        raise ValueError(f"No description in {path}")
    meta_before = text[:idx].rstrip()
    after = text[idx + len("description: |") :]
    m = re.search(r"^(value:|type:|tags:|files:)", after, re.MULTILINE)
    if not m:
        raise ValueError(f"No value: block in {path}")
    body_raw = after[: m.start()]
    body = "\n".join(
        ln[2:] if ln.startswith("  ") else ln
        for ln in body_raw.splitlines()
        if ln.strip() or body_raw.splitlines().index(ln) < len(body_raw.splitlines())
    )
    # Drop stray duplicate 'description: |' lines from broken re-runs
    body_lines = []
    for ln in body.splitlines():
        if ln.strip() == "description: |":
            continue
        body_lines.append(ln)
    body = "\n".join(body_lines).strip()
    rest = after[m.start() :]
    return {"meta_before": meta_before, "body": body, "rest": rest}


def strip_generated_description_parts(body: str) -> str:
    if INTRO_MARKER in body:
        parts = body.split("Pour valider cette introduction")
        if len(parts) > 1:
            after = parts[1].split("\n", 1)
            body = after[1].strip() if len(after) > 1 else ""
    if FLAG_FOOTER_MARKER in body:
        body = body.split(FLAG_FOOTER_MARKER)[0].rstrip()
    # Remove duplicate italic hint lines from re-runs
    lines = body.splitlines()
    cleaned: list[str] = []
    prev = None
    for ln in lines:
        if ln == prev and ln.startswith("*Le drapeau"):
            continue
        cleaned.append(ln)
        prev = ln
    return "\n".join(cleaned).strip()


def write_challenge_yml(path: Path, meta_before: str, description: str, rest: str) -> None:
    lines = [meta_before, "description: |"]
    for line in description.splitlines():
        lines.append("  " + line if line else "  ")
    path.write_text("\n".join(lines) + "\n" + rest.lstrip("\n"), encoding="utf-8")


def load_data102(work: Path) -> Path:
    data_dir = work / "data_102"
    if data_dir.is_dir():
        return data_dir
    work.mkdir(parents=True, exist_ok=True)
    with tarfile.open(DATA102_GZ, "r:gz") as tf:
        tf.extractall(work, filter="data")
    return data_dir


def build_data102_delivery(work: Path) -> Path:
    """Create data_102_delivery tree for find/grep finals."""
    root = work / "data_102_delivery"
    if root.exists():
        shutil.rmtree(root)
    nested = root / "datasets"
    nested.mkdir(parents=True)

    rows_a = [
        "id,ip,note",
        "1,192.168.10.5,valid",
        "2,0.153.42.12,invalid prefix",
        "3,10.20.30.40,valid",
        "4,12.0.7.0,invalid suffix",
        "5,203.0.113.9,valid",
    ]
    (nested / "hosts_a.csv").write_text("\n".join(rows_a) + "\n", encoding="utf-8")
    (nested / "hosts_b.csv").write_text("id,ip\n6,172.16.0.1\n", encoding="utf-8")
    (root / "empty.csv").write_text("", encoding="utf-8")
    rows_c = [
        "name,value,ip",
        "x,1,8.8.8.8",
        "y,2,0.0.0.1",
        "z,3,192.168.0.0",
    ]
    (nested / "metrics.csv").write_text("\n".join(rows_c) + "\n", encoding="utf-8")
    return root


def package_tar(src_dir: Path, dest_tar: Path) -> None:
    with tarfile.open(dest_tar, "w") as tf:
        tf.add(src_dir, arcname=src_dir.name)


def csv_rows(path: Path) -> list[list[str]]:
    text = path.read_text(encoding="utf-8-sig")
    return list(csv.reader(io.StringIO(text)))


def extract_ips_from_row(row: list[str]) -> str | None:
    for cell in reversed(row):
        cell = cell.strip()
        if re.match(r"^[\d.]+$", cell) and cell.count(".") == 3:
            return cell
    return None


def ip_valid(ip: str) -> bool:
    if ip.startswith("0."):
        return False
    if ip.endswith(".0"):
        return False
    return True


def compute_delivery_finals(delivery: Path) -> dict:
    csv_files = sorted(delivery.rglob("*.csv"))
    line_counts: dict[str, int] = {}
    empty_count = 0
    all_lines: list[str] = []
    all_ips: list[str] = []

    for p in csv_files:
        content = p.read_text(encoding="utf-8-sig")
        lines = [ln for ln in content.splitlines() if ln.strip()]
        line_counts[str(p.relative_to(delivery))] = len(lines)
        if len(lines) == 0:
            empty_count += 1
        for row in csv_rows(p):
            if row and row[0].lower() in ("id", "name", "student_id"):
                if any(h.lower() in ("ip", "id", "name") for h in row):
                    continue
            all_lines.append(",".join(row))
            ip = extract_ips_from_row(row)
            if ip:
                all_ips.append(ip)

    valid_ips = sorted({ip for ip in all_ips if ip_valid(ip)})
    invalid_ips = sorted({ip for ip in all_ips if not ip_valid(ip)})

    return {
        "csv_file_count": len(csv_files),
        "empty_csv_count": empty_count,
        "all_data_line_count": len(all_lines),
        "valid_ip_count": len(valid_ips),
        "invalid_ip_count": len(invalid_ips),
        "valid_ips": valid_ips,
        "invalid_ips": invalid_ips,
    }


def home_ls_stats() -> dict:
    all_names = [p for p in HOME42.iterdir() if p.name not in (".", "..")]
    visible = [p.name for p in all_names if not p.name.startswith(".")]
    hidden = [p.name for p in all_names if p.name.startswith(".")]
    memo1_size = (HOME42 / "memo1.txt").stat().st_size
    dir_count = sum(1 for p in HOME42.iterdir() if p.is_dir())
    return {
        "visible_count": len(visible),
        "all_count": len(all_names),
        "hidden_count": len(hidden),
        "memo1_size": memo1_size,
        "dir_count": dir_count,
        "hidden_names": hidden,
    }


def compute_data102_answers(data: Path) -> dict:
    flights = data / "flights.csv"
    grades = data / "grades.csv"
    cars = data / "cars.csv"
    wonderland = data / "wonderland.txt"

    def rows(path: Path) -> list[list[str]]:
        return csv_rows(path)

    fl = rows(flights)
    header = fl[0]
    fl_data = fl[1:]
    idx = {h: i for i, h in enumerate(header)}

    aa7566_line = next(r for r in fl_data if r[idx["flight_number"]] == "AA7566")
    arrivals_942 = [r[idx["flight_number"]] for r in fl_data if r[idx["arrival_time"]] == "9:42 PM"]
    af_cdg_cai = next(
        r[idx["flight_number"]]
        for r in fl_data
        if r[idx["airline_name"]] == "Air France"
        and r[idx["departure_airport"]] == "CDG"
        and r[idx["arrival_airport"]] == "CAI"
    )
    flight_count = len(fl_data)
    air_france_count = sum(1 for r in fl_data if r[idx["airline_name"]] == "Air France")
    wonderland_words = len(wonderland.read_text(encoding="utf-8").split())

    gr = rows(grades)
    gr_data = [r for r in gr[1:] if r and r[0].strip()]
    last5 = gr_data[-5:]
    last5_ids = " ".join(r[0] for r in last5)

    sorted_fl = sorted(fl_data, key=lambda r: r[idx["arrival_airport"]])
    last_ticket = sorted_fl[-1][idx["ticket_price"]].replace("$", "").strip()

    on_time = [r for r in fl_data if r[idx["flight_status"]] == "on-time"]
    on_time_sorted = sorted(on_time, key=lambda r: int(r[idx["passenger_count"]]))
    cheapest_on_time_price = on_time_sorted[0][idx["ticket_price"]].replace("$", "").strip()

    car_brands = sorted({r[1] for r in rows(cars)[1:]})

    return {
        "aa7566_line": ",".join(aa7566_line),
        "arrival_942_flight": arrivals_942[0],
        "arrival_942_alt": arrivals_942[1] if len(arrivals_942) > 1 else None,
        "af_cdg_cai": af_cdg_cai,
        "flight_count": flight_count,
        "air_france_count": air_france_count,
        "wonderland_words": wonderland_words,
        "last_ticket_arrival_sort": last_ticket,
        "cheapest_on_time_price": cheapest_on_time_price,
        "car_brands_unique": len(car_brands),
        "grades_last5_ids": last5_ids,
        "grades_last_student": last5[-1][1],
    }


def build_specs(home: dict, d102: dict, delivery: dict) -> dict[str, dict]:
    root_entries = {p.name for p in ROOTFS.iterdir()}
    missing_from_list = [x for x in ("app", "bin", "etc", "home", "var") if x not in root_entries]

    return {
        "shell_101/00_intro": {
            "flag": flag("pret a commencer"),
            "intro": "101",
            "writeup": "Soumettez le drapeau d'accueil après lecture de l'introduction.",
        },
        "shell_101/a_execution_commandes": {
            "flag": mcq_flag("B"),
            "mcq": True,
            "writeup": """\
1. Tapez `cal` puis Entrée — un calendrier du mois courant s'affiche.
2. QCM : **B** — Affiche un calendrier.
3. Drapeau : `shell1{B}`.""",
        },
        "shell_101/b_arguments_commande": {
            "flag": flag("cal -y"),
            "hint_extra": "Le drapeau est la commande exacte pour afficher l'année entière.",
            "writeup": """\
1. `cal --help` ou `man cal`.
2. Option année complète : `cal -y` (BusyBox/Alpine).
3. Drapeau = commande tapée : `cal -y`.""",
        },
        "shell_101/c01_ls": {
            "flag": flag(f"{home['visible_count']} {home['hidden_count']} {home['memo1_size']} {home['dir_count']}"),
            "hint_extra": "Le drapeau concatène : éléments visibles, fichiers cachés (hors . et ..), taille de memo1.txt en octets, nombre de répertoires.",
            "writeup": f"""\
1. `ls` → {home['visible_count']} entrées visibles.
2. `ls -a` → fichiers cachés (sans `.` et `..`) : {', '.join(home['hidden_names'])} → **{home['hidden_count']}** cachés.
3. `ls -l memo1.txt` → taille **{home['memo1_size']}** octets.
4. `ls -l` → **{home['dir_count']}** répertoires (code, links, memos, works).
5. Drapeau : `shell1{{{home['visible_count']} {home['hidden_count']} {home['memo1_size']} {home['dir_count']}}}`.""",
        },
        "shell_101/c02_whoami": {
            "flag": flag("user42"),
            "writeup": "`whoami` affiche **user42** sur la VM du atelier.",
        },
        "shell_101/c03_pwd": {
            "flag": flag("/home/user42"),
            "writeup": "Dans le répertoire personnel, `pwd` affiche `/home/user42`.",
        },
        "shell_101/c04_cd": {
            "flag": flag(missing_from_list[0] if missing_from_list else "app"),
            "writeup": f"""\
1. `cd /tmp` puis `ls ..` (ou `ls /`).
2. Racine de la VM de l'atelier : {', '.join(sorted(root_entries))}.
3. Parmi app, bin, etc, home, var — absent ici : **{missing_from_list[0]}**.""",
        },
        "shell_101/c05_mkdir": {
            "flag": flag("101"),
            "writeup": "Après `cd` puis `mkdir 101`, le dossier de travail s'appelle **101**.",
        },
        "shell_101/d01_cp": {
            "flag": flag("101 pret"),
            "writeup": "Copiez memo1.txt, memo2.txt, memos/, .secret1.txt, .secret2.txt, links/, works/, code/ dans ~/101 puis vérifiez avec `ls -a ~/101`.",
        },
        "shell_101/d02_mv": {
            "flag": flag("wikipedia_linux ubuntu"),
            "writeup": "Déplacez les memos dans memos/, renommez qrcode1→wikipedia_linux et qrcode2→ubuntu dans links/, rendez les fichiers cachés visibles (mv ou mv depuis .secret*).",
        },
        "shell_101/e01_cat": {
            "flag": mcq_flag("B"),
            "mcq": True,
            "writeup": """\
1. `cat .secret1.txt` — le fichier décrit l'autocomplétion avec **Tab**.
2. QCM : **B** — Appuyer sur Tab (autocomplétion).
3. Drapeau : `shell1{B}`.""",
        },
        "shell_101/e02_micro": {
            "flag": flag("convaincre un chat que je suis le chef"),
            "writeup": "Éditez memo2.txt : supprimez le doublon, ajoutez la ligne sur le chat, enregistrez. Le drapeau est cette ligne.",
        },
        "shell_101/e03_rm": {
            "flag": flag("essay1 code"),
            "writeup": "`rm works/essay1.txt` puis `rm -r code/` dans ~/101.",
        },
        "shell_101/e04_archivage": {
            "flag": flag("tar ok"),
            "writeup": "Lisez `tar -cf` et `tar -czf` ; pas de livrable unique — drapeau de validation de lecture.",
        },
        "shell_101/livrable_1": {
            "flag": mcq_flag("B"),
            "mcq": True,
            "writeup": """\
1. `cd ~ && tar -cf delivery_101.tar 101`
2. Copie cachée : `cp delivery_101.tar /mnt/host/.delivery_101.tar`
3. QCM : **B** — `.delivery_101.tar`
4. Drapeau : `shell1{B}`.""",
        },
        "shell_102/00_intro": {
            "flag": flag("shell 102 start"),
            "intro": "102",
            "writeup": "Drapeau d'accueil Shell 102.",
        },
        "shell_102/pipe_redirection": {
            "flag": flag("pipe ok"),
            "writeup": "Lisez la section sur stdin/stdout, `|` et `>` ; drapeau de validation.",
        },
        "shell_102/preliminaire_tar": {
            "flag": flag("data_102"),
            "writeup": "`tar -xf data_102.tar` puis `cd data_102`.",
        },
        "shell_102/preliminaire_csv": {
            "flag": flag("csv ok"),
            "writeup": "Comprenez le format CSV (colonnes séparées par des virgules, ligne d'en-tête).",
        },
        "shell_102/grep_aa7566": {
            "flag": mcq_flag("B"),
            "mcq": True,
            "writeup": """\
1. `grep AA7566 flights.csv > flight_AA7566_info.txt` (ou redirection équivalente).
2. QCM : **B** — `flight_AA7566_info.txt`.
3. Drapeau : `shell1{B}`.""",
        },
        "shell_102/grep_arrival_942": {
            "flag": mcq_flag("B"),
            "mcq": True,
            "writeup": f"""\
1. Arrivée 21h42 = `9:42 PM` dans flights.csv → **{d102['arrival_942_flight']}**.
2. QCM : **B** — SQ6943.
3. Drapeau : `shell1{{B}}`.""",
        },
        "shell_102/grep_af_cdg_cai": {
            "flag": mcq_flag("B"),
            "mcq": True,
            "writeup": f"""\
1. Air France CDG→CAI → **{d102['af_cdg_cai']}**.
2. QCM : **B** — AF3301.
3. Drapeau : `shell1{{B}}`.""",
        },
        "shell_102/wc": {
            "flag": flag(f"{d102['flight_count']} {d102['air_france_count']} {d102['wonderland_words']}"),
            "writeup": f"""\
- Vols (sans en-tête) : {d102['flight_count']}
- Vols Air France : {d102['air_france_count']}
- Mots wonderland.txt : {d102['wonderland_words']}""",
        },
        "shell_102/sort": {
            "flag": flag(d102["last_ticket_arrival_sort"]),
            "hint_extra": "Triez flights.csv par aéroport d'arrivée (-t, -k4) ; le drapeau est le prix du dernier vol.",
            "writeup": f"`sort -t, -k4 flights.csv | tail -1` → prix **{d102['last_ticket_arrival_sort']}** (sans le symbole $ dans le drapeau).",
        },
        "shell_102/head_tail": {
            "flag": flag(d102["grades_last_student"]),
            "hint_extra": "Le drapeau reprend le nom de l'étudiant de la dernière ligne parmi les 5 dernières de grades.csv.",
            "writeup": f"`tail -5 grades.csv` → dernière ligne : **{d102['grades_last_student']}** (Elvina Elderfield).",
        },
        "shell_102/cut": {
            "flag": flag("grades_only cars_without_personal_info"),
            "writeup": "Créez grades_only.txt (dernière colonne) et cars_without_personal_info.csv (4 premières colonnes).",
        },
        "shell_102/uniq": {
            "flag": flag(str(d102["car_brands_unique"])),
            "writeup": f"`cut ... | sort | uniq` sur la colonne marque → **{d102['car_brands_unique']}** marques uniques.",
        },
        "shell_102/sed": {
            "flag": flag("w0nd3rl4nd.txt"),
            "writeup": "`sed 's/Alice/4l1c3/g' wonderland.txt > w0nd3rl4nd.txt`.",
        },
        "shell_102/livrable_2_prerequis": {
            "flag": flag("data_102_delivery"),
            "writeup": "`tar -xf data_102_delivery.tar` puis `cd data_102_delivery`.",
        },
        "shell_102/find_xargs": {
            "flag": flag(
                f"{delivery['csv_file_count']} {delivery['empty_csv_count']} {delivery['all_data_line_count']}"
            ),
            "writeup": f"""\
1. Compter les .csv : **{delivery['csv_file_count']}** fichiers.
2. CSV vides : **{delivery['empty_csv_count']}**.
3. Lignes dans all_data.csv (concat de tous les CSV) : **{delivery['all_data_line_count']}**.""",
        },
        "shell_102/grep_avance": {
            "flag": flag(f"{delivery['valid_ip_count']} {delivery['invalid_ip_count']}"),
            "writeup": f"""\
1. Filtrer IP valides / invalides (0.… ou finissant par .0).
2. Valides : {delivery['valid_ip_count']} — {', '.join(delivery['valid_ips'][:5])}…
3. Invalides : {delivery['invalid_ip_count']} — {', '.join(delivery['invalid_ips'])}.""",
        },
    }


def main() -> None:
    work = ROOT / ".gen_work"
    work.mkdir(exist_ok=True)
    data102 = load_data102(work)
    delivery_root = build_data102_delivery(work)
    delivery_stats = compute_delivery_finals(delivery_root)
    home = home_ls_stats()
    d102 = compute_data102_answers(data102)
    specs = build_specs(home, d102, delivery_stats)

    # Package archives into challenge folders
    prelim_tar = CHALLENGES / "shell_102/preliminaire_tar"
    prelim_tar.mkdir(parents=True, exist_ok=True)
    with tarfile.open(DATA102_GZ, "r:gz") as gz:
        with tarfile.open(prelim_tar / "data_102.tar", "w") as out:
            for member in gz.getmembers():
                out.addfile(member, gz.extractfile(member))

    livrable2 = CHALLENGES / "shell_102/livrable_2_prerequis"
    livrable2.mkdir(parents=True, exist_ok=True)
    package_tar(delivery_root, livrable2 / "data_102_delivery.tar")

  # Update files: in challenge.yml for those two
    for folder, spec in specs.items():
        ch_dir = CHALLENGES / folder
        ch_dir.mkdir(parents=True, exist_ok=True)
        private = ch_dir / "private"
        private.mkdir(parents=True, exist_ok=True)
        display_flag = write_flag_files(private, spec)
        (private / "writeup.md").write_text(
            f"# Writeup — {folder}\n\n{spec['writeup'].strip()}\n\n**Flag :** `{display_flag}`\n",
            encoding="utf-8",
        )

        yml_path = ch_dir / "challenge.yml"
        if not yml_path.is_file():
            print(f"  skip (no yml): {folder}")
            continue
        parsed = parse_challenge_yml(yml_path)
        body = strip_generated_description_parts(parsed["body"])

        intro_key = spec.get("intro")
        if intro_key == "101":
            description = INTRO_101 + body
        elif intro_key == "102":
            description = INTRO_102 + body
        else:
            extra = spec.get("hint_extra", "")
            footer = MCQ_FOOTER if spec.get("mcq") else FLAG_FOOTER
            if extra:
                footer = f"\n\n*{extra}*\n" + footer
            description = body + footer

        write_challenge_yml(yml_path, parsed["meta_before"], description, parsed["rest"])

        # Ensure files: lists archives
        if folder == "shell_102/preliminaire_tar":
            patch_files_list(yml_path, ["data_102.tar"])
        elif folder == "shell_102/livrable_2_prerequis":
            patch_files_list(yml_path, ["data_102_delivery.tar"])

        print(f"  {folder} → {display_flag}")

    n_txt = len(list(CHALLENGES.rglob("private/flag.txt")))
    n_yml = len(list(CHALLENGES.rglob("private/flag.yml")))
    n_wu = len(list(CHALLENGES.rglob("private/writeup.md")))
  # placeholder manifest for docker-compose bind mount
    deploy_dir = CHALLENGES / ".deploy"
    deploy_dir.mkdir(parents=True, exist_ok=True)
    (deploy_dir / "flag_specs.json").write_text(
        '{"_root": "' + str(CHALLENGES.resolve()).replace("\\", "\\\\") + '"}\n',
        encoding="utf-8",
    )
    print(f"\n{ n_txt } flag.txt, {n_yml} flag.yml, {n_wu} writeups")


def patch_files_list(yml_path: Path, files: list[str]) -> None:
    text = yml_path.read_text(encoding="utf-8")
    if "files:" in text:
        text = re.sub(r"files:\n(?:  - .+\n)+", "", text)
    text = text.rstrip() + "\nfiles:\n" + "".join(f"  - {f}\n" for f in files)
    yml_path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
