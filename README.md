# Neuroslop League — `.github`

Organization profile repository for **[Neuroslop-League](https://github.com/Neuroslop-League)**.

- The organization's public profile README (shown on `github.com/Neuroslop-League`) lives in [`profile/README.md`](profile/README.md).
- The banner and per-member contribution cards live in [`assets/`](assets/) and are rebuilt automatically every 6 hours by [`.github/workflows/stats.yml`](.github/workflows/stats.yml).

## Adding members to the contribution chart

Because GitHub's standard `GITHUB_TOKEN` cannot always enumerate private organization memberships, the roster is maintained explicitly in [`members.txt`](members.txt) — one GitHub username per line:

```text
RUdolf1517
username2
username3
```

Any public org members returned by the API are included automatically as well. After updating [`members.txt`](members.txt), wait for the next scheduled run, trigger **Actions → league stats cards → Run workflow**, or regenerate locally:

```bash
python3 scripts/gen_banner.py
GITHUB_TOKEN="$(gh auth token)" python3 scripts/gen_org_stats.py
```

## Contribution chart preview

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/commits-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/commits-light.svg">
  <img src="assets/commits-dark.svg" alt="Neuroslop League member contributions over the last 12 months" width="100%">
</picture>
