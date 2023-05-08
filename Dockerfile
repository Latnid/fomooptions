# 使用基于 selenium/standalone-chrome:dev 镜像作为基础镜像
FROM optionweb:1.0

# 设置工作目录
#WORKDIR /app

# 复制应用程序代码到镜像中
#COPY . .

#docker run 命令：
#docker run -it -p 4444:4444 -p 7900:7900 -p 8501-8510:8501-8510 --shm-size 2g -v /Users/dintal/Desktop/DockContainer/OptionsAnalysisWeb:/app/ optionsweb:1.6