# OpUpdate Oracle deployment notes

This updater now depends on a recent Selenium browser image because Barchart
blocks the old Chromium 114 / ChromeDriver 114 stack with CloudFront 403.

The Oracle host at `138.2.122.78` is ARM64 (`aarch64`) and uses
`docker-compose` v1. Use `selenium/standalone-chromium:latest` there, not the
amd64-only Chrome image.

The GitHub repo path is `OpUpdate/`. The current Oracle server path is
`/mnt/apps/OptionsUpdate/`; keep that server directory name unless you also
change `/mnt/apps/docker-compose.yml`.

## Files to update on Oracle

Copy these repo files into `/mnt/apps/OptionsUpdate/`:

- `OpUpdate/Modules/DataAutoDownload.py`
- `OpUpdate/Modules/CleanData.py`
- `OpUpdate/Dockerfile`
- `OpUpdate/requirements.txt`
- `OpUpdate/docker/data-download.conf`
- `OpUpdate/.dockerignore`

The server's `/mnt/apps/docker-compose.yml` also needs the `OptionsUpdate`
service to build from the local directory:

```yaml
OptionsUpdate:
  build:
    context: ./OptionsUpdate
```

Keep the server's existing `.env` values unless you are intentionally changing
credentials or database host settings.

## Rebuild and restart only OptionsUpdate

On the Oracle server, make sure `/mnt/apps/OptionsUpdate/Dockerfile` starts
with:

```dockerfile
FROM selenium/standalone-chromium:latest
```

Then from `/mnt/apps`:

```bash
sudo docker-compose build OptionsUpdate
sudo docker rm -f apps_OptionsUpdate_1
sudo docker-compose up -d --no-deps OptionsUpdate
```

The explicit `docker rm` avoids a `docker-compose` v1 / Docker 29
`ContainerConfig` recreate bug. PostgreSQL and OpWeb remain running.

## Verify versions

```bash
sudo docker exec apps_OptionsUpdate_1 sh -lc \
  "python3 - <<'PY'
import selenium, pandas
print('selenium', selenium.__version__)
print('pandas', pandas.__version__)
PY
chromium --version
chromedriver --version"
```

Expected shape:

- Selenium Python `4.43.0`
- Chromium and ChromeDriver both `147.x` or another matching current pair

## One-time download smoke test

Stop the scheduled updater first so it does not compete for the single browser
session:

```bash
sudo docker exec apps_OptionsUpdate_1 supervisorctl stop data-download
sudo docker exec \
  -e OPTIONSUPDATE_RUN_ONCE=1 \
  -e OPTIONSUPDATE_IGNORE_MARKET_HOURS=1 \
  -e OPTIONSUPDATE_SKIP_DATABASE_WRITE=1 \
  apps_OptionsUpdate_1 \
  python3 /app/Modules/DataAutoDownload.py
sudo docker exec apps_OptionsUpdate_1 supervisorctl start data-download
```

Check for four files for the same date:

```bash
find OptionsUpdate/Data/Increase OptionsUpdate/Data/Decrease -maxdepth 1 \
  -name '*change-in-open-interest-*.csv' -printf '%f %s\n' | sort | tail
```

## One-time download plus database write

Use this only when you want to backfill the latest Barchart export immediately:

```bash
sudo docker exec apps_OptionsUpdate_1 supervisorctl stop data-download
sudo docker exec \
  -e OPTIONSUPDATE_RUN_ONCE=1 \
  -e OPTIONSUPDATE_IGNORE_MARKET_HOURS=1 \
  apps_OptionsUpdate_1 \
  python3 /app/Modules/DataAutoDownload.py
sudo docker exec apps_OptionsUpdate_1 supervisorctl start data-download
```

## Debug files

If Barchart blocks the browser or the page layout changes again, the updater
saves HTML and screenshots under:

```text
OptionsUpdate/Modules/debug/
```

The error log remains:

```text
OptionsUpdate/Modules/Datadownload_error.log
```