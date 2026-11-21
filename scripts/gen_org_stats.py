#!/usr/bin/env python3
"""Render the org-wide commit-activity card for the Neuroslop League profile README.

Same card as the maintainer's personal one, but aggregated over every league
member: pulls each member's last 12 months of contribution data from the
GitHub GraphQL API, sums the numbers across the roster and writes two
theme-matched SVG files:

    assets/commits-dark.svg
    assets/commits-light.svg

The roster is `members.txt` at the repo root (one GitHub login per line).
Public members of the org, if the token is allowed to see them, are added
automatically; anything the API refuses is simply skipped. If the roster ends
up empty the script exits with a clear message.

Standard library only, so the workflow needs no pip install:

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

W, H = 1000, 250
MONTHS_BACK = 12


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
    """Roster = members.txt ∪ whatever the API lets us see of the org."""
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
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
      commitContributionsByRepository(maxRepositories:25) {
        repository { nameWithOwner }
        contributions(first:1) { totalCount }
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
    """First month of the trailing window, so totals and bars cover the same span."""
    index = today.year * 12 + (today.month - 1) - (months - 1)
    return index // 12, index % 12 + 1


def collect_member(token: str, login: str, start: dt.datetime, end: dt.datetime) -> dict | None:
    fmt = lambda d: d.isoformat().replace("+00:00", "Z")  # noqa: E731
    year = gql(YEAR_QUERY, {"login": login, "from": fmt(start), "to": fmt(end)}, token)
    if not year or not year.get("user"):
        print(f"warning: skipping {login!r} (API returned nothing)", file=sys.stderr)
        return None
    data = year["user"]["contributionsCollection"]

    days = [
        (d["date"], d["contributionCount"])
        for week in data["contributionCalendar"]["weeks"]
        for d in week["contributionDays"]
    ]
    days.sort()

    months = []
    year_, month = start.year, start.month
    today = end.date()
    while (year_, month) <= (today.year, today.month):
        m_start, m_end = month_bounds(year_, month)
        month_data = gql(MONTH_QUERY, {
            "login": login,
            "from": fmt(m_start),
            "to": fmt(min(m_end, end)),
        }, token)
        commits = 0
        if month_data and month_data.get("user"):
            commits = month_data["user"]["contributionsCollection"]["totalCommitContributions"]
        months.append((year_, month, commits))
        year_, month = (year_ + 1, 1) if month == 12 else (year_, month + 1)

    repos = [r["repository"]["nameWithOwner"] for r in data["commitContributionsByRepository"]]

    return dict(
        login=login,
        commits=data["totalCommitContributions"],
        prs=data["totalPullRequestContributions"],
        issues=data["totalIssueContributions"],
        reviews=data["totalPullRequestReviewContributions"],
        days=days,
        months=months,
        repos=repos,
    )


def collect(token: str, today: dt.date) -> dict:
    logins = discover_members(token)
    if not logins:
        sys.exit(f"No members found. Put GitHub logins into {MEMBERS_FILE} or grant the token org read access.")

    start, _ = month_bounds(*first_month_of_window(today))
    end = dt.datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=dt.timezone.utc)

    members = [m for m in (collect_member(token, login, start, end) for login in logins) if m]
    if not members:
        sys.exit("None of the roster members returned contribution data.")

    # Sum everything across the roster.
    commits = sum(m["commits"] for m in members)
    prs = sum(m["prs"] for m in members)
    issues = sum(m["issues"] for m in members)
    reviews = sum(m["reviews"] for m in members)
    repos = sorted({repo for m in members for repo in m["repos"]})

    day_sum: dict[str, int] = {}
    for m in members:
        for date, count in m["days"]:
            day_sum[date] = day_sum.get(date, 0) + count
    days = sorted(day_sum.items())

    active_days = sum(1 for _, count in days if count > 0)
    busiest_date, busiest_count = max(days, key=lambda x: x[1], default=(None, 0))

    longest = current = 0
    for _, count in days:
        current = current + 1 if count > 0 else 0
        longest = max(longest, current)
    trailing = 0
    for _, count in reversed(days):
        if count == 0:
            break
        trailing += 1

    months_map: dict[tuple[int, int], int] = {}
    for m in members:
        for year, month, count in m["months"]:
            months_map[(year, month)] = months_map.get((year, month), 0) + count
    months = sorted((y, mo, c) for (y, mo), c in months_map.items())

    most_active = max(members, key=lambda m: m["commits"], default=None)

    return dict(
        org=ORG,
        member_count=len(members),
        commits=commits,
        prs=prs,
        issues=issues,
        reviews=reviews,
        repos=len(repos),
        active_days=active_days,
        longest_streak=longest,
        current_streak=trailing,
        busiest_date=busiest_date,
        busiest_count=busiest_count,
        months=months,
        most_active=(most_active["login"], most_active["commits"]) if most_active else None,
        updated=today.isoformat(),
    )


# --------------------------------------------------------------------- rendering

def nf(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def human_date(iso: str | None) -> str:
    if not iso:
        return "—"
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b')}"


def stat_block(x: float, value: int, label: str, t: dict) -> str:
    return f"""    <text x="{x}" y="132" font-family="{SANS}" font-size="42" font-weight="700" letter-spacing="-1" fill="{t['text']}">{nf(value)}</text>
    <text x="{x + 1}" y="152" font-family="{MONO}" font-size="10.5" letter-spacing="1.7" fill="{t['label']}">{label}</text>"""


def render(d: dict, name: str) -> str:
    t = THEMES[name]

    chart_x, chart_w, chart_base, chart_h = 560, 384, 186, 100
    bars = d["months"]
    gap = 9
    bar_w = (chart_w - gap * (len(bars) - 1)) / len(bars)
    peak = max((c for *_, c in bars), default=1) or 1

    bar_svg = []
    for i, (year, month, commits) in enumerate(bars):
        x = chart_x + i * (bar_w + gap)
        is_current = i == len(bars) - 1
        h = max(2.5, chart_h * commits / peak) if commits else 2.5
        y = chart_base - h
        fill = t["stub"] if commits == 0 else (t["bar_accent"] if is_current else t["bar"])
        rx = min(3, h / 2)
        bar_svg.append(
            f'      <rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="{rx:.1f}" fill="{fill}">'
            f'<title>{commits} commits · {dt.date(year, month, 1).strftime("%B %Y")}</title></rect>'
        )
        if commits:
            bar_svg.append(
                f'      <text x="{x + bar_w / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle" '
                f'font-family="{MONO}" font-size="9.5" fill="{t["muted"]}">{commits}</text>'
            )
        bar_svg.append(
            f'      <text x="{x + bar_w / 2:.1f}" y="{chart_base + 17}" text-anchor="middle" '
            f'font-family="{MONO}" font-size="9.5" fill="{t["label"]}">'
            f'{dt.date(year, month, 1).strftime("%b")}</text>'
        )

    facts = "  ·  ".join([
        f'{d["active_days"]} active days',
        f'longest streak {d["longest_streak"]} d',
        f'busiest day {d["busiest_count"]} ({human_date(d["busiest_date"])})',
    ])

    top_line = ""
    if d["most_active"]:
        login, count = d["most_active"]
        top_line = (
            f'    <text x="56" y="212" font-family="{MONO}" font-size="11" fill="{t["muted"]}">'
            f'most active: {login} — {nf(count)} commits  ·  {d["repos"]} repositories</text>'
        )

    bars_svg = "\n".join(bar_svg)

    first = dt.date(bars[0][0], bars[0][1], 1)
    last = dt.date(bars[-1][0], bars[-1][1], 1)
    span = f'{first.strftime("%b %Y")} → {last.strftime("%b %Y")}'

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="stitle">
  <title id="stitle">Commit activity for all Neuroslop League members: {d['commits']} commits and {d['prs']} pull requests over the last 12 months</title>
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
    <ellipse cx="40" cy="20" rx="300" ry="190" fill="url(#glowA)"/>
    <ellipse cx="960" cy="240" rx="300" ry="180" fill="url(#glowB)"/>

    <text x="56" y="46" font-family="{MONO}" font-size="11" letter-spacing="3.2" fill="{t['amber']}">COMMITS &#183; ALL MEMBERS &#183; LAST 12 MONTHS</text>
{stat_block(56, d['commits'], 'COMMITS', t)}
{stat_block(224, d['prs'], 'PULL REQUESTS', t)}
{stat_block(392, d['member_count'], 'MEMBERS', t)}
    <path d="M212 74 v82" stroke="{t['hair']}" stroke-width="1"/>
    <path d="M380 74 v82" stroke="{t['hair']}" stroke-width="1"/>
    <text x="56" y="190" font-family="{MONO}" font-size="11" fill="{t['muted']}">{facts}</text>
{top_line}
    <text x="56" y="236" font-family="{MONO}" font-size="9.5" fill="{t['label']}">updated {d['updated']}</text>

    <text x="{chart_x}" y="46" font-family="{MONO}" font-size="10.5" letter-spacing="2.6" fill="{t['label']}">COMMIT ACTIVITY</text>
    <text x="{chart_x + chart_w}" y="46" text-anchor="end" font-family="{MONO}" font-size="9.5" fill="{t['label']}">{span}</text>
{bars_svg}
    <path d="M{chart_x} {chart_base + 0.5} h{chart_w}" stroke="{t['hair']}" stroke-width="1"/>
    <text x="{chart_x + chart_w}" y="232" text-anchor="end" font-family="{MONO}" font-size="9.5" fill="{t['label']}">commits per month</text>
  </g>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18" fill="none" stroke="{t['border']}" stroke-width="1"/>
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

    print(f"members={data['member_count']} commits={data['commits']} prs={data['prs']} "
          f"repos={data['repos']} active_days={data['active_days']} longest={data['longest_streak']}")


if __name__ == "__main__":
    main()
