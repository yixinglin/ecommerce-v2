# 使用官方 Python 3.12 镜像作为基础镜像
FROM python:3.12-slim

# 复制项目文件到容器中的工作目录
ADD . /code

# 设置工作目录
WORKDIR /code

# 进入工作目录
RUN cd /code

# 安装项目依赖
RUN apt-get update
RUN apt-get install fonts-wqy-zenhei -y
# RUN pip install --no-cache-dir -r requirements.txt
RUN --mount=type=cache,target=/root/.cache pip install -r requirements.txt

# 暴露应用端口
EXPOSE 5018

# 启动应用
CMD ["python", "/code/main.py"]