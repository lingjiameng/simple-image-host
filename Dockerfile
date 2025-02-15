# 1、从官方 Python 基础镜像开始
FROM python:3.9-slim

# 2、将当前工作目录设置为 /code
# 这是放置 requirements.txt 文件和应用程序目录的地方
WORKDIR /code

# 3、先复制 requirements.txt 文件
# 由于这个文件不经常更改，Docker 会检测它并在这一步使用缓存，也为下一步启用缓存
COPY ./requirements.txt /code/requirements.txt

# 4、运行 pip 命令安装依赖项
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 5、复制 FastAPI 项目代码
COPY ./app /app

# 6、运行服务
CMD ["python", "/app/main.py"]