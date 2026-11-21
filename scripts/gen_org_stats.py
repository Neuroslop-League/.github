#!/usr/bin/env python3
"""Render the per-member contribution card for the Neuroslop League profile README.

Pulls the last 12 months of contribution data from the GitHub GraphQL API for
every member in the roster (`members.txt` + any org members visible to the
token) and renders two theme-matched SVG cards:

    assets/commits-dark.svg
    assets/commits-light.svg

Each member gets a color-coded row (commits, PRs, share, horizontal bar) on
the left and a matching stacked segment in the 12-month bar chart on the right.

Standard library only:

    GITHUB_TOKEN=... python3 scripts/gen_org_stats.py
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ORG = os.environ.get("NEUROSLOP_ORG", "Neuroslop-League")
API = "https://api.github.com/graphql"
REST = "https://api.github.com"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
MEMBERS_FILE = ROOT / "members.txt"

from theme import MONO, SANS, THEMES  # noqa: E402

W = 1000
MONTHS_BACK = 12
ROW_Y0 = 74
ROW_H = 44


# ---------------------------------------------------------------- data fetching

def gql(query: str, variables: dict, token: str) -> dict | None:
    """GraphQL call that returns None instead of dying on error."""
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "league-stats-card",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read())
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None
    if "errors" in payload or "data" not in payload or payload["data"] is None:
        return None
    return payload["data"]


def rest(path: str, token: str) -> list | None:
    req = urllib.request.Request(
        f"{REST}{path}",
        headers={
            "Authorization": f"bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "league-stats-card",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None


def parse_members_file() -> list[str]:
    logins: list[str] = []
    if not MEMBERS_FILE.exists():
        return logins
    for raw in MEMBERS_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            logins.append(line.lstrip("@"))
    return logins


def discover_members(token: str) -> list[str]:
    """Roster = members.txt + whatever public/org members the API returns."""
    seen = {login.lower(): login for login in parse_members_file()}

    data = gql(
        "query($org:String!) { organization(login:$org) { "
        "membersWithRole(first:100) { nodes { login } } } }",
        {"org": ORG},
        token,
    )
    if data:
        for node in (data.get("organization") or {}).get("membersWithRole", {}).get("nodes", []):
            login = node.get("login")
            if login:
                seen.setdefault(login.lower(), login)

    public = rest(f"/orgs/{ORG}/public_members", token) or []
    for node in public:
        login = node.get("login")
        if login:
            seen.setdefault(login.lower(), login)

    return list(seen.values())


YEAR_QUERY = """
query($login:String!, $from:DateTime!, $to:DateTime!) {
  user(login:$login) {
    contributionsCollection(from:$from, to:$to) {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
      commitContributionsByRepository(maxRepositories:25) {
        repository { nameWithOwner }
      }
    }
  }
}
"""

MONTH_QUERY = """
query($login:String!, $from:DateTime!, $to:DateTime!) {
  user(login:$login) {
    contributionsCollection(from:$from, to:$to) { totalCommitContributions }
  }
}
"""


def month_bounds(year: int, month: int) -> tuple[dt.datetime, dt.datetime]:
    start = dt.datetime(year, month, 1, tzinfo=dt.timezone.utc)
    end = (start.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(seconds=1)
    return start, end


def first_month_of_window(today: dt.date, months: int = MONTHS_BACK) -> tuple[int, int]:
    index = today.year * 12 + (today.month - 1) - (months - 1)
    return index // 12, index % 12 + 1


def collect_member(token: str, login: str, start: dt.datetime, end: dt.datetime) -> dict | None:
    fmt = lambda d: d.isoformat().replace("+00:00", "Z")  # noqa: E731
    year = gql(YEAR_QUERY, {"login": login, "from": fmt(start), "to": fmt(end)}, token)
    if not year or not year.get("user"):
        print(f"warning: skipping {login!r} (API returned nothing)", file=sys.stderr)
        return None
    data = year["user"]["contributionsCollection"]

    active_days = sum(
        1
        for week in data["contributionCalendar"]["weeks"]
        for d in week["contributionDays"]
        if d["contributionCount"] > 0
    )

    months: list[tuple[int, int, int]] = []
    y_, m_ = start.year, start.month
    today = end.date()
    while (y_, m_) <= (today.year, today.month):
        m_start, m_end = month_bounds(y_, m_)
        month_data = gql(MONTH_QUERY, {
            "login": login,
            "from": fmt(m_start),
            "to": fmt(min(m_end, end)),
        }, token)
        commits = 0
        if month_data and month_data.get("user"):
            commits = month_data["user"]["contributionsCollection"]["totalCommitContributions"]
        months.append((y_, m_, commits))
        y_, m_ = (y_ + 1, 1) if m_ == 12 else (y_, m_ + 1)

    repos = [r["repository"]["nameWithOwner"] for r in data["commitContributionsByRepository"]]

    return dict(
        login=login,
        commits=data["totalCommitContributions"],
        prs=data["totalPullRequestContributions"],
        issues=data["totalIssueContributions"],
        reviews=data["totalPullRequestReviewContributions"],
        active_days=active_days,
        months=months,
        repos=len(repos),
    )


def collect(token: str, today: dt.date) -> dict:
    logins = discover_members(token)
    if not logins:
        sys.exit(f"No members found. Add GitHub logins to {MEMBERS_FILE} or grant org read access.")

    start, _ = month_bounds(*first_month_of_window(today))
    end = dt.datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=dt.timezone.utc)

    members = [m for m in (collect_member(token, login, start, end) for login in logins) if m]
    if not members:
        sys.exit("None of the roster members returned contribution data.")

    # Sort by commits descending, then PRs descending, then login ascending.
    members.sort(key=lambda m: (-m["commits"], -m["prs"], m["login"].lower()))

    month_keys = [(y, mo) for y, mo, _ in members[0]["months"]]

    return dict(
        org=ORG,
        members=members,
        month_keys=month_keys,
        total_commits=sum(m["commits"] for m in members),
        total_prs=sum(m["prs"] for m in members),
        updated=today.isoformat(),
    )


# --------------------------------------------------------------------- rendering

def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def nf(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def trunc_login(login: str, limit: int = 18) -> str:
    return login if len(login) <= limit else login[: limit - 1] + "…"


def render(d: dict, name: str) -> str:
    t = THEMES[name]
    palette = t["members"]
    members = d["members"]
    month_keys = d["month_keys"]

    h = max(260, ROW_Y0 + len(members) * ROW_H + 48)
    left_x, right_edge = 56, 512
    bar_x = 74
    track_w = right_edge - bar_x

    max_commits = max((m["commits"] for m in members), default=1) or 1
    total_commits = d["total_commits"] or 1

    member_svg = []
    for i, m in enumerate(members):
        color = palette[i % len(palette)]
        y0 = ROW_Y0 + i * ROW_H
        share = round(100 * m["commits"] / total_commits) if d["total_commits"] else 0
        fill_w = max(6.0, track_w * m["commits"] / max_commits) if m["commits"] else 0.0
        display_name = esc(trunc_login(m["login"]))

        member_svg.append(
            f'    <g>\n'
            f'      <title>@{esc(m["login"])}: {nf(m["commits"])} commits, {nf(m["prs"])} PRs, '
            f'{m["repos"]} repos, {m["active_days"]} active days ({share}%)</title>\n'
            f'      <circle cx="{left_x + 6}" cy="{y0 + 11}" r="4.5" fill="{color}"/>\n'
            f'      <text x="{bar_x}" y="{y0 + 15}" font-family="{SANS}" font-size="13.5" font-weight="600" fill="{t["text"]}">@{display_name}</text>\n'
            f'      <text x="{right_edge}" y="{y0 + 15}" text-anchor="end">'
            f'<tspan font-family="{SANS}" font-size="13.5" font-weight="700" fill="{t["text"]}">{nf(m["commits"])}</tspan>'
            f'<tspan font-family="{MONO}" font-size="10" fill="{t["muted"]}"> commits &#183; {nf(m["prs"])} PRs &#183; {share}%</tspan>'
            f'</text>\n'
            f'      <rect x="{bar_x}" y="{y0 + 24}" width="{track_w}" height="7" rx="3.5" fill="{t["stub"]}"/>\n'
            + (
                f'      <rect x="{bar_x}" y="{y0 + 24}" width="{fill_w:.1f}" height="7" rx="3.5" fill="{color}"/>\n'
                if fill_w > 0 else ""
            )
            + f'    </g>'
        )

    # Stacked 12-month bar chart on the right.
    chart_x, chart_w = 556, 388
    chart_top, chart_base = 84, h - 56
    chart_h = chart_base - chart_top
    gap = 9
    bar_w = (chart_w - gap * (len(month_keys) - 1)) / len(month_keys)

    month_totals = [
        sum(m["months"][mi][2] for m in members)
        for mi in range(len(month_keys))
    ]
    peak = max(month_totals, default=1) or 1

    clip_defs = []
    bar_svg = []
    for mi, (year, month) in enumerate(month_keys):
        x = chart_x + mi * (bar_w + gap)
        total = month_totals[mi]
        total_h = max(2.5, chart_h * total / peak) if total else 2.5
        bar_y = chart_base - total_h
        rx = min(3.0, total_h / 2)

        if total == 0:
            bar_svg.append(
                f'      <rect x="{x:.1f}" y="{bar_y:.1f}" width="{bar_w:.1f}" height="{total_h:.1f}" '
                f'rx="{rx:.1f}" fill="{t["stub"]}">'
                f'<title>0 commits · {dt.date(year, month, 1).strftime("%B %Y")}</title></rect>'
            )
        else:
            clip_id = f"mbar-{mi}"
            clip_defs.append(
                f'    <clipPath id="{clip_id}">'
                f'<rect x="{x:.1f}" y="{bar_y:.1f}" width="{bar_w:.1f}" height="{total_h:.1f}" rx="{rx:.1f}"/>'
                f'</clipPath>'
            )
            segs = []
            cursor = float(chart_base)
            breakdown = []
            for idx, m in enumerate(members):
                cnt = m["months"][mi][2]
                if cnt <= 0:
                    continue
                seg_h = total_h * cnt / total
                seg_y = cursor - seg_h
                color = palette[idx % len(palette)]
                segs.append(
                    f'        <rect x="{x:.1f}" y="{seg_y:.2f}" width="{bar_w:.1f}" height="{seg_h + 0.4:.2f}" fill="{color}"/>'
                )
                breakdown.append(f"@{m['login']}: {cnt}")
                cursor = seg_y

            tip = f'{dt.date(year, month, 1).strftime("%B %Y")} ({nf(total)} commits): ' + ", ".join(breakdown)
            bar_svg.append(
                f'      <g clip-path="url(#{clip_id})">\n'
                f'        <title>{esc(tip)}</title>\n'
                + "\n".join(segs)
                + '\n      </g>'
            )
            bar_svg.append(
                f'      <text x="{x + bar_w / 2:.1f}" y="{bar_y - 7:.1f}" text-anchor="middle" '
                f'font-family="{MONO}" font-size="9.5" fill="{t["muted"]}">{total}</text>'
            )

        bar_svg.append(
            f'      <text x="{x + bar_w / 2:.1f}" y="{chart_base + 17}" text-anchor="middle" '
            f'font-family="{MONO}" font-size="9.5" fill="{t["label"]}">'
            f'{dt.date(year, month, 1).strftime("%b")}</text>'
        )

    first = dt.date(month_keys[0][0], month_keys[0][1], 1)
    last = dt.date(month_keys[-1][0], month_keys[-1][1], 1)
    span = f'{first.strftime("%b %Y")} → {last.strftime("%b %Y")}'

    member_word = "member" if len(members) == 1 else "members"
    footer_left = (
        f'{len(members)} {member_word} &#183; '
        f'{nf(d["total_commits"])} commits &#183; '
        f'{nf(d["total_prs"])} PRs &#183; '
        f'updated {d["updated"]}'
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-labelledby="stitle">
  <title id="stitle">Neuroslop League member contributions over the last 12 months ({len(members)} {member_word}, {nf(d['total_commits'])} commits)</title>
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
    <clipPath id="frame"><rect x="1" y="1" width="{W - 2}" height="{h - 2}" rx="18"/></clipPath>
{chr(10).join(clip_defs)}
  </defs>

  <g clip-path="url(#frame)">
    <rect width="{W}" height="{h}" fill="url(#bg)"/>
    <rect width="{W}" height="{h}" fill="url(#dots)"/>
    <ellipse cx="40" cy="20" rx="300" ry="190" fill="url(#glowA)"/>
    <ellipse cx="960" cy="{h - 10}" rx="300" ry="180" fill="url(#glowB)"/>

    <text x="{left_x}" y="46" font-family="{MONO}" font-size="11" letter-spacing="3.0" fill="{t['amber']}">CONTRIBUTIONS &#183; BY MEMBER &#183; LAST 12 MONTHS</text>
{chr(10).join(member_svg)}
    <text x="{left_x}" y="{h - 20}" font-family="{MONO}" font-size="9.5" fill="{t['label']}">{footer_left}</text>

    <path d="M534 34 v{h - 56}" stroke="{t['hair']}" stroke-width="1"/>

    <text x="{chart_x}" y="46" font-family="{MONO}" font-size="10.5" letter-spacing="2.4" fill="{t['label']}">MONTHLY BREAKDOWN</text>
    <text x="{chart_x + chart_w}" y="46" text-anchor="end" font-family="{MONO}" font-size="9.5" fill="{t['label']}">{span}</text>
{chr(10).join(bar_svg)}
    <path d="M{chart_x} {chart_base + 0.5} h{chart_w}" stroke="{t['hair']}" stroke-width="1"/>
    <text x="{chart_x + chart_w}" y="{h - 20}" text-anchor="end" font-family="{MONO}" font-size="9.5" fill="{t['label']}">stacked commits per month</text>
  </g>
  <rect x="1" y="1" width="{W - 2}" height="{h - 2}" rx="18" fill="none" stroke="{t['border']}" stroke-width="1"/>
</svg>
"""


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("Set GITHUB_TOKEN (a token with read access to the GraphQL API).")

    today = dt.date.today()
    data = collect(token, today)

    OUT.mkdir(parents=True, exist_ok=True)
    for theme in ("dark", "light"):
        path = OUT / f"commits-{theme}.svg"
        path.write_text(render(data, theme), encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size} B)")

    print(f"members={len(data['members'])} commits={data['total_commits']} prs={data['total_prs']}")


if __name__ == "__main__":
    main()
