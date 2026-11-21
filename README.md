# Лига Нейрослопа — `.github`

Репозиторий профиля организации **[Neuroslop-League](https://github.com/Neuroslop-League)**.

- Главный README организации (который отображается на странице организации) находится в [`profile/README.md`](profile/README.md).
- Карточки баннера и общей диаграммы коммитов лежат в [`assets/`](assets/) и автоматически пересобираются каждые 6 часов через [`.github/workflows/stats.yml`](.github/workflows/stats.yml).

## Как добавить участников в диаграмму коммитов

GitHub API не всегда отдаёт приватный список участников организации стандартному `GITHUB_TOKEN`, поэтому список участников ведётся явно в файле [`members.txt`](members.txt) — по одному GitHub-логину в строке:

```text
RUdolf1517
username2
username3
```

Публичных участников организации скрипт подхватывает дополнительно сам. После правки [`members.txt`](members.txt) можно либо подождать следующего запуска workflow, либо запустить пересборку вручную во вкладке **Actions → league stats cards → Run workflow**, либо локально:

```bash
python3 scripts/gen_banner.py
GITHUB_TOKEN="$(gh auth token)" python3 scripts/gen_org_stats.py
```

## Превью диаграммы

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/commits-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/commits-light.svg">
  <img src="assets/commits-dark.svg" alt="Диаграмма коммитов всех участников Лиги Нейрослопа" width="100%">
</picture>
