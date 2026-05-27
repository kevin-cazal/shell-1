#!/usr/bin/env python3
"""Export CTFd challenge ratings/reviews and admin comments to TODO_comments.md."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URL = "http://localhost:9042/ctfd/default"
DEFAULT_TOKEN = (
    "ctfd_0cb2ccac1f05fd0d545f187bb21bed7a7a630eb974a47e6d2c76ce69f7736afa"
)
DEFAULT_OUTPUT = ROOT / "TODO_comments.md"


def _api_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
    }


def _get_json(
    session: requests.Session,
    url: str,
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    r = session.get(url, params=params, timeout=30)
    r.raise_for_status()
    body = r.json()
    if not body.get("success", True):
        raise RuntimeError(f"API error at {url}: {body}")
    return body


def verify_token(session: requests.Session, base_url: str) -> str:
    body = _get_json(session, f"{base_url}/api/v1/users/me")
    name = body.get("data", {}).get("name")
    if not name:
        raise RuntimeError("API token rejected or /users/me returned no name")
    return name


def fetch_challenges(session: requests.Session, base_url: str) -> dict[int, str]:
    body = _get_json(
        session,
        f"{base_url}/api/v1/challenges",
        params={"view": "admin"},
    )
    out: dict[int, str] = {}
    for ch in body.get("data", []):
        cid = ch.get("id")
        name = ch.get("name")
        if isinstance(cid, int) and name:
            out[cid] = name
    return out


def paginate(
    session: requests.Session,
    url: str,
    *,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page = 1
    base_params = dict(params or {})
    while True:
        body = _get_json(session, url, params={**base_params, "page": page})
        items.extend(body.get("data", []))
        pagination = body.get("meta", {}).get("pagination", {})
        nxt = pagination.get("next")
        if not nxt:
            break
        page = int(nxt)
    return items


def fetch_all_ratings(
    session: requests.Session,
    base_url: str,
    challenges: dict[int, str],
) -> list[tuple[str, int, dict[str, Any], list[dict[str, Any]]]]:
    """Return (challenge_name, challenge_id, summary, ratings) per challenge with ratings."""
    results: list[tuple[str, int, dict[str, Any], list[dict[str, Any]]]] = []
    for cid, name in sorted(challenges.items(), key=lambda x: x[0]):
        page = 1
        ratings: list[dict[str, Any]] = []
        summary: dict[str, Any] = {}
        while True:
            body = _get_json(
                session,
                f"{base_url}/api/v1/challenges/{cid}/ratings",
                params={"page": page},
            )
            ratings.extend(body.get("data", []))
            summary = body.get("meta", {}).get("summary", summary)
            pagination = body.get("meta", {}).get("pagination", {})
            nxt = pagination.get("next")
            if not nxt:
                break
            page = int(nxt)
        if ratings:
            results.append((name, cid, summary, ratings))
    return sorted(results, key=lambda x: x[1])


def fetch_all_comments(session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return paginate(session, f"{base_url}/api/v1/comments")


def _escape_md_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _user_name(row: dict[str, Any]) -> str:
    user = row.get("user") or {}
    if isinstance(user, dict) and user.get("name"):
        return str(user["name"])
    author = row.get("author") or {}
    if isinstance(author, dict) and author.get("name"):
        return str(author["name"])
    uid = row.get("user_id") or row.get("author_id")
    return f"user #{uid}" if uid is not None else "unknown"


def _vote_label(value: Any) -> str:
    if value == 1:
        return "+1"
    if value == -1:
        return "-1"
    return str(value) if value is not None else "—"


def _comment_sort_key(row: dict[str, Any]) -> tuple[int, int]:
    """Sort admin comments by challenge id when applicable."""
    ctype = str(row.get("type") or "standard")
    if ctype == "challenge" and row.get("challenge_id") is not None:
        return (0, int(row["challenge_id"]))
    if ctype == "user" and row.get("user_id") is not None:
        return (1, int(row["user_id"]))
    if ctype == "team" and row.get("team_id") is not None:
        return (2, int(row["team_id"]))
    if ctype == "page" and row.get("page_id") is not None:
        return (3, int(row["page_id"]))
    return (4, int(row.get("id") or 0))


def _comment_target(
    row: dict[str, Any],
    challenges: dict[int, str],
) -> str:
    ctype = row.get("type") or "standard"
    if ctype == "challenge" and row.get("challenge_id") is not None:
        cid = int(row["challenge_id"])
        label = challenges.get(cid, f"challenge #{cid}")
        return f"Challenge: {label} (id {cid})"
    if ctype == "user" and row.get("user_id") is not None:
        return f"User id {row['user_id']}"
    if ctype == "team" and row.get("team_id") is not None:
        return f"Team id {row['team_id']}"
    if ctype == "page" and row.get("page_id") is not None:
        return f"Page id {row['page_id']}"
    return ctype


def render_markdown(
    base_url: str,
    admin_name: str,
    challenges: dict[int, str],
    ratings_by_challenge: list[tuple[str, int, dict[str, Any], list[dict[str, Any]]]],
    comments: list[dict[str, Any]],
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# CTFd feedback export",
        "",
        f"- **Instance:** {base_url}",
        f"- **Exported:** {now}",
        f"- **Authenticated as:** {admin_name}",
        f"- **Challenges:** {len(challenges)}",
        "",
        "## Challenge ratings & reviews",
        "",
        "Participant upvotes/downvotes and optional review text (admin-only in CTFd).",
        "",
    ]

    if not ratings_by_challenge:
        lines.append("*(none)*")
        lines.append("")
    else:
        for name, cid, summary, ratings in ratings_by_challenge:
            up = summary.get("up", "—")
            down = summary.get("down", "—")
            count = summary.get("count", len(ratings))
            lines.append(f"### {name}")
            lines.append("")
            lines.append(f"Challenge id: {cid} · summary: +{up} / −{down} ({count} rating(s))")
            lines.append("")
            lines.append("| User | Vote | Review | Date |")
            lines.append("| --- | --- | --- | --- |")
            for row in ratings:
                review = (row.get("review") or "").strip() or "—"
                date = row.get("date") or "—"
                lines.append(
                    "| "
                    + " | ".join(
                        _escape_md_cell(x)
                        for x in (
                            _user_name(row),
                            _vote_label(row.get("value")),
                            review,
                            str(date),
                        )
                    )
                    + " |"
                )
            lines.append("")

    lines.extend(
        [
            "## Admin comments",
            "",
            "Organizer discussion (CTFd `/api/v1/comments`, admin-only).",
            "",
        ]
    )

    if not comments:
        lines.append("*(none)*")
        lines.append("")
    else:
        by_type: dict[str, list[dict[str, Any]]] = {}
        for row in comments:
            ctype = str(row.get("type") or "standard")
            by_type.setdefault(ctype, []).append(row)

        for ctype in sorted(by_type.keys()):
            lines.append(f"### Type: `{ctype}`")
            lines.append("")
            for row in sorted(by_type[ctype], key=_comment_sort_key):
                target = _comment_target(row, challenges)
                author = _user_name(row)
                date = row.get("date") or "—"
                content = (row.get("content") or "").strip()
                lines.append(f"#### {target}")
                lines.append("")
                lines.append(f"- **Author:** {author}")
                lines.append(f"- **Date:** {date}")
                lines.append(f"- **Comment id:** {row.get('id', '—')}")
                lines.append("")
                if content:
                    if "\n" in content:
                        lines.append("```")
                        lines.append(content)
                        lines.append("```")
                    else:
                        lines.append(content)
                else:
                    lines.append("*(empty)*")
                lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("CTFD_URL", DEFAULT_URL))
    parser.add_argument(
        "--token",
        default=os.environ.get("CTFD_TOKEN", DEFAULT_TOKEN),
        help="Admin API token (CTFD_TOKEN or PRESET_ADMIN_TOKEN)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output markdown path",
    )
    args = parser.parse_args()
    base_url = args.url.rstrip("/")

    session = requests.Session()
    session.headers.update(_api_headers(args.token))

    try:
        admin_name = verify_token(session, base_url)
        print(f"Authenticated as {admin_name!r}")
        challenges = fetch_challenges(session, base_url)
        print(f"Found {len(challenges)} challenge(s)")
        ratings = fetch_all_ratings(session, base_url, challenges)
        total_ratings = sum(len(r[3]) for r in ratings)
        print(f"Found {total_ratings} rating(s) across {len(ratings)} challenge(s)")
        comments = fetch_all_comments(session, base_url)
        print(f"Found {len(comments)} admin comment(s)")
        md = render_markdown(
            base_url, admin_name, challenges, ratings, comments
        )
        args.output.write_text(md, encoding="utf-8")
        print(f"Wrote {args.output}")
    except requests.RequestException as e:
        print(f"HTTP error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
