FROM python:3.12-slim

# 国内镜像加速：pip 走清华源，Playwright 浏览器走 npmmirror。
# 海外服务器构建时可覆盖回官方源：
#   docker compose build --build-arg PIP_INDEX_URL=https://pypi.org/simple --build-arg PLAYWRIGHT_DOWNLOAD_HOST=
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_INDEX_URL=${PIP_INDEX_URL}
ARG PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright
ENV PLAYWRIGHT_DOWNLOAD_HOST=${PLAYWRIGHT_DOWNLOAD_HOST}

WORKDIR /app

# apt 换国内源（playwright --with-deps 装 Chromium 系统依赖用；海外构建可删除本行）
RUN sed -i 's@deb.debian.org@mirrors.tuna.tsinghua.edu.cn@g; s@security.debian.org@mirrors.tuna.tsinghua.edu.cn@g' /etc/apt/sources.list.d/debian.sources

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install --with-deps chromium

COPY app ./app
COPY sql ./sql
COPY docker-entrypoint.sh /usr/local/bin/glavk-entrypoint.sh
RUN chmod 755 /usr/local/bin/glavk-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/glavk-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
