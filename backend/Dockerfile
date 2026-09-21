FROM python:3.12-slim

# 国内镜像加速：pip 和 apt 走清华源，Playwright 的 Chromium 走 npmmirror。
# 海外服务器构建时可覆盖：--build-arg PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_INDEX_URL=${PIP_INDEX_URL}

# Playwright 从 cdn.playwright.dev 下载 Chromium，实际会 302 到 storage.googleapis.com，
# 国内实测 167MB 要一小时以上（Chromium + headless shell 合计约 270MB）。
# npmmirror 有同样的 Chrome-for-Testing 文件，但路径段不同，所以按浏览器分别改下载源。
# ffmpeg 只有 2.3MB，继续走官方 CDN，不值得为它再引一个镜像地址。
ARG CHROMIUM_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/chrome-for-testing
ENV PLAYWRIGHT_CHROMIUM_DOWNLOAD_HOST=${CHROMIUM_DOWNLOAD_HOST}
ENV PLAYWRIGHT_CHROMIUM_HEADLESS_SHELL_DOWNLOAD_HOST=${CHROMIUM_DOWNLOAD_HOST}

WORKDIR /app

# apt 换国内源（playwright --with-deps 装 Chromium 系统依赖用；海外构建可删除本行）
RUN sed -i 's@deb.debian.org@mirrors.tuna.tsinghua.edu.cn@g; s@security.debian.org@mirrors.tuna.tsinghua.edu.cn@g' /etc/apt/sources.list.d/debian.sources

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 不需要网页截图时可以 --build-arg INSTALL_CHROMIUM=false 跳过：构建从十几分钟降到两分钟，
# 镜像也小很多。跳过后卡片会退回首字母图标，截图失败不影响项目保存。
ARG INSTALL_CHROMIUM=true
RUN if [ "$INSTALL_CHROMIUM" = "true" ]; then \
        playwright install --with-deps chromium; \
    else \
        echo "INSTALL_CHROMIUM=false: 跳过 Chromium，网页截图功能不可用"; \
    fi

COPY app ./app
COPY docker-entrypoint.sh /usr/local/bin/glavk-entrypoint.sh
# Strip Windows CRLF in case the build context came from a Windows checkout/archive,
# otherwise the shebang "#!/bin/sh\r" breaks with "no such file or directory".
RUN sed -i 's/\r$//' /usr/local/bin/glavk-entrypoint.sh && chmod 755 /usr/local/bin/glavk-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/glavk-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
