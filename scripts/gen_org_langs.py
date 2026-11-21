#!/usr/bin/env python3
"""Render the org language-split cards and sync the Projects table in profile/README.md.

Aggregates bytes of code per language across all public, non-fork, non-archived
repositories in the Neuroslop League organization and writes two monochrome
theme-matched SVGs:

    assets/langs-dark.svg
    assets/langs-light.svg

Also refreshes the `<!-- PROJECTS:START --> ... <!-- PROJECTS:END -->` table in
`profile/README.md` from the organization's public repositories (excluding `.github`).

Standard library only:

    GITHUB_TOKEN=... python3 scripts/gen_org_langs.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from theme import MONO, THEMES

ORG = os.environ.get("NEUROSLOP_ORG", "Neuroslop-League")
API = "https://api.github.com/graphql"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
PROFILE_README = ROOT / "profile" / "README.md"

W, H = 1000, 230
TOP_N = 6

QUERY = """
query($org:String!, $cursor:String) {
  organization(login:$org) {
    repositories(first:100, after:$cursor, isFork:false, privacy:PUBLIC, orderBy:{field:STARGAZERS, direction:DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        description
        url
        isArchived
        stargazerCount
        pushedAt
        primaryLanguage { name }
        languages(first:12, orderBy:{field:SIZE, direction:DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""


def gql(query: str, variables: dict, token: str) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "league-langs-card",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read())
    except urllib.error.HTTPError as exc:  # pragma: no cover - network only
        sys.exit(f"GitHub API error {exc.code}: {exc.read().decode()[:400]}")
    if "errors" in payload or not payload.get("data"):
        sys.exit(f"GraphQL errors: {payload.get('errors')}")
    return payload["data"]


def collect(token: str) -> dict:
    totals: dict[str, int] = {}
    repos_with_code = 0
    projects: list[dict] = []
    cursor = None

    while True:
        org_data = gql(QUERY, {"org": ORG, "cursor": cursor}, token)["organization"]
        if not org_data:
            sys.exit(f"Organization {ORG!r} not found.")
        repo_conn = org_data["repositories"]
        for repo in repo_conn["nodes"]:
            if repo.get("isArchived"):
                continue
            edges = repo["languages"]["edges"]
            if edges:
                repos_with_code += 1
            for edge in edges:
                name = edge["node"]["name"]
                totals[name] = totals.get(name, 0) + edge["size"]
            if repo["name"] != ".github":
                projects.append(repo)
        if not repo_conn["pageInfo"]["hasNextPage"]:
            break
        cursor = repo_conn["pageInfo"]["endCursor"]

    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    top = ranked[:TOP_N]
    rest = sum(size for _, size in ranked[TOP_N:])
    total = sum(size for _, size in ranked)
    if rest:
        top.append(("Other", rest))

    # Sort projects by stars descending, then most recently pushed.
    projects.sort(key=lambda r: (-r["stargazerCount"], r.get("pushedAt") or ""), reverse=False)

    return {
        "languages": top,
        "total": total,
        "repos": repos_with_code,
        "projects": projects,
    }


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def human_bytes(n: int) -> str:
    return f"{n / 1_000_000:.1f} MB" if n >= 1_000_000 else f"{n / 1_000:.1f} kB"


def render(d: dict, theme: str) -> str:
    t = THEMES[theme]
    palette = t["members"]

    x0, bar_w, bar_y, bar_h = 56, 888, 66, 26
    gap = 3.0
    total = d["total"] or 1
    langs = d["languages"]

    segments = []
    legend = []
    if not langs:
        segments.append(
            f'      <rect x="{x0}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="4" fill="{t["stub"]}"/>'
        )
        legend.append(
            f'      <text x="{x0}" y="140" font-family="{MONO}" font-size="12" fill="{t["muted"]}">'
            f'No language bytes indexed yet across public org repositories.</text>'
        )
    else:
        usable = bar_w - gap * (len(langs) - 1)
        x = float(x0)
        for i, (name, size) in enumerate(langs):
            color = palette[i % len(palette)]
            width = max(4.0, usable * size / total)
            segments.append(
                f'      <rect x="{x:.1f}" y="{bar_y}" width="{width:.1f}" height="{bar_h}" rx="4" fill="{color}">'
                f'<title>{esc(name)} — {size / total * 100:.1f}%</title></rect>'
            )
            x += width + gap

        col_w = bar_w / 4
        for i, (name, size) in enumerate(langs):
            color = palette[i % len(palette)]
            row, col = divmod(i, 4)
            cx = x0 + col * col_w
            cy = 136 + row * 34
            pct = size / total * 100
            legend.append(
                f'      <circle cx="{cx + 5:.1f}" cy="{cy - 4:.1f}" r="5" fill="{color}"/>'
                f'<text x="{cx + 19:.1f}" y="{cy}" font-family="{MONO}" font-size="12.5" fill="{t["text_soft"]}">{esc(name)}</text>'
                f'<text x="{cx + col_w - 26:.1f}" y="{cy}" text-anchor="end" font-family="{MONO}" font-size="12" fill="{t["muted"]}">'
                f'{pct:.1f}%</text>'
            )

    repo_word = "repo" if d["repos"] == 1 else "repos"
    summary = f"{d['repos']} {repo_word} &#183; {human_bytes(d['total'])} of code"
    title_summary = ", ".join(f"{n} {s / total * 100:.0f}%" for n, s in langs) or "pending repositories"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="lt">
  <title id="lt">Language split across {d['repos']} public {ORG} repositories: {esc(title_summary)}</title>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{t['bg0']}"/><stop offset="1" stop-color="{t['bg1']}"/>
    </linearGradient>
    <radialGradient id="glowA" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{t['amber']}" stop-opacity="{t['amber_op']}"/>
      <stop offset="1" stop-color="{t['amber']}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glowB" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{t['blue']}" stop-opacity="{t['blue_op']}"/>
      <stop offset="1" stop-color="{t['blue']}" stop-opacity="0"/>
    </radialGradient>
    <pattern id="dots" width="21" height="21" patternUnits="userSpaceOnUse">
      <circle cx="1.5" cy="1.5" r="1.05" fill="{t['dot']}" fill-opacity="{t['dot_op']}"/>
    </pattern>
    <clipPath id="frame"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18"/></clipPath>
  </defs>

  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#bg)"/>
    <rect width="{W}" height="{H}" fill="url(#dots)"/>
    <ellipse cx="60" cy="10" rx="300" ry="150" fill="url(#glowA)"/>
    <ellipse cx="950" cy="{H}" rx="300" ry="150" fill="url(#glowB)"/>

    <text x="{x0}" y="44" font-family="{MONO}" font-size="11" letter-spacing="3.2" fill="{t['amber']}">LANGUAGES &#183; PUBLIC ORG REPOS</text>
    <text x="{x0 + bar_w}" y="44" text-anchor="end" font-family="{MONO}" font-size="10" fill="{t['label']}">{summary}</text>

{chr(10).join(segments)}
{chr(10).join(legend)}

    <path d="M{x0} 196 h{bar_w}" stroke="{t['hair']}" stroke-width="1"/>
    <text x="{x0}" y="216" font-family="{MONO}" font-size="9.5" fill="{t['label']}">bytes per language across {ORG} &#183; top {TOP_N} + other</text>
  </g>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18" fill="none" stroke="{t['border']}" stroke-width="1"/>
</svg>
"""


def format_projects_table(projects: list[dict]) -> str:
    header = [
        "| Project | What it is | Stack | Stars |",
        "| :--- | :--- | :--- | ---: |",
    ]
    if not projects:
        header.append(
            f"| **[Neuroslop-League](https://github.com/orgs/{ORG}/repositories)** | "
            "*No standalone project repositories yet — new public org repos will appear here automatically.* | "
            "`AI` `Open Source` | — |"
        )
        return "\n".join(header)

    rows = []
    for r in projects:
        desc = (r.get("description") or "*No description yet — probably vibe-coded at 3 AM.*").replace("|", "\\|").strip()
        lang_names = [e["node"]["name"] for e in r["languages"]["edges"][:3]]
        if not lang_names and r.get("primaryLanguage"):
            lang_names = [r["primaryLanguage"]["name"]]
        stack = " ".join(f"`{name}`" for name in lang_names) if lang_names else "—"
        stars = f"★ {r['stargazerCount']}"
        rows.append(f"| **[{r['name']}]({r['url']})** | {desc} | {stack} | {stars} |")
    return "\n".join(header + rows)


def sync_profile_readme(projects: list[dict]) -> bool:
    if not PROFILE_README.exists():
        return False
    text = PROFILE_README.read_text(encoding="utf-8")
    pattern = re.compile(r"(<!-- PROJECTS:START -->\n).*?(\n<!-- PROJECTS:END -->)", re.DOTALL)
    if not pattern.search(text):
        return False
    table = format_projects_table(projects)
    updated = pattern.sub(rf"\1{table}\2", text, count=1)
    if updated == text:
        return False
    PROFILE_README.write_text(updated, encoding="utf-8")
    return True


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("Set GITHUB_TOKEN (a token with read access to the GraphQL API).")

    data = collect(token)
    OUT.mkdir(parents=True, exist_ok=True)
    for theme in ("dark", "light"):
        path = OUT / f"langs-{theme}.svg"
        path.write_text(render(data, theme), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size} B)")

    if sync_profile_readme(data["projects"]):
        print(f"updated {PROFILE_README.relative_to(ROOT)} ({len(data['projects'])} project repos)")

    print(", ".join(f"{n}={s / (data['total'] or 1) * 100:.1f}%" for n, s in data["languages"]))


if __name__ == "__main__":
    main()
