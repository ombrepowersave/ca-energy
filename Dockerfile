# --- 基础镜像 ---
# 使用一个轻量级的官方 Python 3.10 镜像
FROM python:3.12-slim

# --- 设置工作目录 ---
# 在容器内创建一个 /app 目录，并将后续命令都在此执行
WORKDIR /app

# --- 安装依赖 ---
# 1. 仅复制依赖文件
COPY requirements.txt .
# 2. 安装依赖
# --no-cache-dir: 不存储缓存，减小镜像体积
# --trusted-host pypi.python.org: (可选) 有时在国内服务器访问pypi较慢，这有助于提高稳定性
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

# --- 复制项目代码 ---
# 将当前目录下的所有文件复制到容器的 /app 目录
COPY . .

# --- 暴露端口 ---
# 声明容器将监听 5000 端口 (Gunicorn 默认运行在此端口)
EXPOSE 5000

# --- 启动命令 ---
# 当容器启动时，执行此命令
# 使用 gunicorn 启动 app.py 中的 'app' 实例
# -w 4: 启动 4 个工作进程 (可以根据服务器CPU调整)
# -b 0.0.0.0:5000: 监听所有网络接口的 5000 端口
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]