# glavk 服务器 Docker 部署教程

本文按 Ubuntu 22.04/24.04 编写。默认端口为：前端 `6222`、API `6555`。前端 nginx 会在 Docker 内部代理 `/api`，后端默认只绑定服务器本机，远程用户只需要访问前端端口。

数据库默认外接：Compose 不内置 MariaDB，`.env` 中的 `DATABASE_URL` 需要指向你自己的 MariaDB 实例（服务器自装、云数据库或其他容器均可）。如需改用内置数据库，见第 3 步的可选说明。

## 1. 准备服务器

服务器需要一个客户端可以访问的 IPv4 地址。浏览器最终打开 `http://服务器IP:6222`，但这个 IP 不需要填写到配置文件中。

安装 Docker Engine 和 Compose 插件：

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"
newgrp docker
docker --version
docker compose version
```

## 2. 获取项目

```bash
git clone https://github.com/1wu-davy-2/glavk.git
cd glavk
```

## 3. 上传并创建唯一配置文件

将仓库中的 `glavk.env.example` 上传到服务器项目目录。它特意不以点开头，适合 Windows 文件管理器、SFTP 面板和网页上传控件拖动上传。以点开头的 `.env.server.example` 属于隐藏文件，部分上传器默认不显示或会拒绝拖动，因此之前会出现上传失败。

进入项目目录后执行：

```bash
cp glavk.env.example .env
nano .env
```

服务器最终只保留并使用项目根目录的 `.env`，前后端不再分别配置。必改的是数据库四要素：

```dotenv
# 必填：指向你自己的 MariaDB，先建好 glavk 库和账号
DB_HOST=数据库主机IP
DB_PORT=3306
DB_USER=数据库账号
DB_PASSWORD=数据库密码
```

数据库密码可以包含 `@ : / ? #` 等任意字符——后端会自动做 URL 编码，按原样填写即可。

端口和管理员账号也建议修改：

```dotenv
FRONTEND_PORT=6222
BACKEND_PORT=6555
ADMIN_USERNAME=admin
ADMIN_PASSWORD=修改为管理员密码
```

密码建议只使用字母、数字和 `._-@!`，避免在 `.env` 中使用未转义的空格、`#` 和换行。其余变量保持模板内容即可。前端通过 nginx 同源转发 `/api`，不需要填写服务器 IP 或 `VITE_API_BASE_URL`。

可选：如果想用 Compose 内置的 MariaDB（不再自己准备数据库），在启动命令上加 `--profile bundled-db`，并把四要素改为 `DB_HOST=mariadb`、`DB_PORT=3306`、`DB_USER=glavk_user`、`DB_PASSWORD` 与 `MARIADB_PASSWORD` 一致，同时修改 `.env` 中的 `MARIADB_PASSWORD` 和 `MARIADB_ROOT_PASSWORD`。内置 MariaDB 宿主机端口为 `3307`，默认只绑定服务器本机。

后端首次启动会把自动生成的 `AUTH_SECRET_KEY`、`CREDENTIAL_ENCRYPTION_KEY` 和 `TRANSPORT_PRIVATE_KEY_B64` 保存到 `backend_data` 卷。不要删除这个卷，否则历史项目密码无法解密，登录 token 也会失效。

## 4. 防火墙

只开放前端端口。后端默认绑定服务器本机，不要对公网开放 `6555`：

```bash
sudo ufw allow OpenSSH
sudo ufw allow 6222/tcp
sudo ufw enable
sudo ufw status
```

## 5. 检查配置并启动

先让 Compose 展开变量，确认没有残留 `CHANGE-`。如果 `.env` 忘了填数据库四要素，这一步会直接报错提示：

```bash
docker compose config > /tmp/glavk-compose.yml
grep -E "BACKEND_BIND_ADDRESS|BACKEND_PORT|FRONTEND_PORT|DATABASE_URL" /tmp/glavk-compose.yml
```

启动服务：

```bash
docker compose up -d --build
docker compose ps
```

首次构建后端镜像会安装 Chromium，可能需要几分钟。等待健康检查：

```bash
curl http://127.0.0.1:6555/api/health
```

应返回：

```json
{"status":"ok","service":"glavk-api"}
```

从客户端浏览器打开前端端口：

```text
http://服务器IP:6222
```

登录后，浏览器请求保持同源，由 nginx 转发到后端；不需要重新填写 API 地址。

## 6. 首次验收

按下面顺序验证：

1. 使用 `.env` 中的管理员账号密码登录。
2. 添加一个不填用户名和密码的静态项目，确认可以保存并出现网页截图或首字母图标。
3. 添加一个带用户名密码的项目，确认卡片只显示掩码。
4. 点击复制密码，确认提示“密码已复制”。
5. 查看 API 和前端日志：

```bash
docker compose logs --tail=100 backend
docker compose logs --tail=100 frontend
```

## 7. 更新和备份

数据库不在 Compose 内时，请按你数据库实例自身的方案定期备份 `glavk` 库（例如云数据库自动备份，或 `mariadb-dump` 定时任务）。

使用内置 MariaDB profile 时可以这样导出：

```bash
mkdir -p backups
docker compose --profile bundled-db exec -T mariadb sh -c 'mariadb-dump -uroot -p"$MARIADB_ROOT_PASSWORD" "$MARIADB_DATABASE"' > "backups/glavk-$(date +%Y%m%d-%H%M%S).sql"
```

同时备份 Docker 卷中的截图和运行时密钥。先查看卷名：

```bash
docker volume ls | grep backend_data
```

然后将实际卷名替换到备份命令：

```bash
docker run --rm -v glavk_backend_data:/data -v "$PWD/backups:/backup" alpine tar czf /backup/glavk-backend-data-$(date +%Y%m%d-%H%M%S).tar.gz -C /data .
```

更新：

```bash
git pull --ff-only
docker compose up -d --build
docker compose ps
```

## 8. 没有 HTTPS 的限制

没有域名和证书时，HTTP 不能防止主动中间人替换前端 JavaScript。项目的 RSA-OAEP + AES-GCM 只降低普通被动抓包直接得到密码的风险，不能替代 HTTPS。没有 HTTPS 时只建议在 localhost、可信内网或 VPN/Tailscale 中使用；公网使用必须在反向代理前配置 HTTPS。
