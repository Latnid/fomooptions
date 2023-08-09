# app/Dockerfile

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip3 install -r requirements.txt

# 将替换的文件复制到容器中 streamlit 1.24.1
#COPY ./Modify/main.ac67fab5.js /usr/local/lib/python3.11/site-packages/streamlit/static/static/js/main.ac67fab5.js

#将替换的文件复制到容器中 streamlit 1.18.0
COPY ./Modify/main.223e9539.js /usr/local/lib/python3.11/site-packages/streamlit/static/static/js/main.223e9539.js
#Modify the index meta / header
COPY ./Modify/index.html /usr/local/lib/python3.11/site-packages/streamlit/static/index.html

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "Free_Tier.py", "--server.port=8501", "--server.address=0.0.0.0"]