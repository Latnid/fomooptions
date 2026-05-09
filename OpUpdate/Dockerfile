FROM selenium/standalone-chromium:latest

USER root

ENV PYTHONUNBUFFERED=1 \
    OPTIONSUPDATE_APP_DIR=/app \
    OPTIONSUPDATE_LOG_DIR=/app/Modules \
    SEL_DOWNLOAD_DIR=/home/seluser/Downloads

COPY requirements.txt /tmp/optionsupdate-requirements.txt
RUN python3 -m pip install --no-cache-dir -r /tmp/optionsupdate-requirements.txt

COPY docker/data-download.conf /etc/supervisor/conf.d/data-download.conf
COPY . /app

RUN mkdir -p /home/seluser/Downloads /app/Modules/debug /app/Data/Increase /app/Data/Decrease \
    && chown -R seluser:root /app /home/seluser/Downloads

USER seluser
