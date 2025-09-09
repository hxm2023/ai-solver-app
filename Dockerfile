# ==============================================================================
# Dockerfile for AI Solver Backend - V1.5 (Final Single-Worker Version)
# ==============================================================================

# 步骤1: 选择一个官方的、带有Python的基础镜像
FROM python:3.11-slim

# 步骤2: 安装系统级依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 步骤3: 设置安全环境变量
ENV TOKENIZERS_PARALLELISM=false
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1

# 步骤4: 创建一个有“家”的普通用户
RUN groupadd -r app && useradd --no-log-init -r -g app -m -d /app app
WORKDIR /app
USER app

# 步骤5: 拷贝和安装依赖
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 步骤6: 拷贝代码
USER root
COPY . /app/
RUN chown -R app:app /app
USER app

# 步骤7: 暴露端口
EXPOSE 7860

# --- 【核心修复】: 使用Gunicorn作为进程管理器来启动Uvicorn工人 ---
CMD ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:7860", "main:app"]