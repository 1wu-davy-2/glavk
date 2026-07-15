# glavk 服务器 Docker 部署教程

本文按 Ubuntu 22.04/24.04 编写。默认端口为：前端 `6222`、API `6555`、MariaDB `3307`。MariaDB 默认只绑定服务器本机，浏览器需要访问 API，因此 API 端口必须允许客户端访问。

## 1. 准备服务器

服务器需要一个客户端可以访问的 IPv4 地址。下面假设服务器地址是 `192.168.1.100`。不要把 `0.0.0.0` 填入 `SERVER_IP`，它只能用于监听，不能作为浏览器访问地址。

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

## 3. 创建唯一配置文件

```bash
cp .env.server.example .env
nano .env
```

只修改这些值：

```dotenv
SERVER_IP=192.168.1.100
FRONTEND_PORT=6222
BACKEND_PORT=6555
MARIADB_PORT=3307
MARIADB_PASSWORD=修改为数据库密码
MARIADB_ROOT_PASSWORD=修改为数据库root密码
ADMIN_USERNAME=admin
ADMIN_PASSWORD=修改为管理员密码
```

密码建议只使用字母、数字和 `._-@!`，避免在 `.env` 中使用未转义的空格、`#` 和换行。其余变量保持模板内容即可。

`VITE_API_BASE_URL` 是构建期配置，最终值应为：

```text
http://192.168.1.100:6555
```

后端首次启动会把自动生成的 `AUTH_SECRET_KEY`、`CREDENTIAL_ENCRYPTION_KEY` 和 `TRANSPORT_PRIVATE_KEY_B64` 保存到 `backend_data` 卷。不要删除这个卷，否则历史项目密码无法解密，登录 token 也会失效。

## 4. 防火墙

只开放前端和 API。不要对公网开放 MariaDB 的 `3307`：

```bash
sudo ufw allow OpenSSH
sudo ufw allow 6222/tcp
sudo ufw allow 6555/tcp
sudo ufw enable
sudo ufw status
```

如果只允许内网访问 API，可以把第二条替换为实际网段，例如：

```bash
sudo ufw delete allow 6555/tcp
sudo ufw allow from 192.168.1.0/24 to any port 6555 proto tcp
```

## 5. 检查配置并启动

先让 Compose 展开变量，确认没有残留 `CHANGE-` 或错误 IP：

```bash
docker compose --env-file .env config > /tmp/glavk-compose.yml
grep -E "VITE_API_BASE_URL|CORS_ORIGINS|BACKEND_PORT|FRONTEND_PORT" /tmp/glavk-compose.yml
```

启动服务：

```bash
docker compose --env-file .env up -d --build
docker compose --env-file .env ps
```

首次构建后端镜像会安装 Chromium，可能需要几分钟。等待健康检查：

```bash
curl http://127.0.0.1:6555/api/health
```

应返回：

```json
{"status":"ok","service":"glavk-api"}
```

从客户端浏览器打开：

```text
http://192.168.1.100:6222
```

登录后，在浏览器开发者工具 Network 中可以看到请求地址是 `http://192.168.1.100:6555/api/...`。如果仍然请求旧 IP，说明 frontend 没有重新构建，重新执行：

```bash
docker compose --env-file .env build --no-cache frontend
docker compose --env-file .env up -d frontend
```

## 6. 首次验收

按下面顺序验证：

1. 使用 `.env` 中的管理员账号密码登录。
2. 添加一个不填用户名和密码的静态项目，确认可以保存并出现网页截图或首字母图标。
3. 添加一个带用户名密码的项目，确认卡片只显示掩码。
4. 点击复制密码，确认提示“密码已复制”。
5. 查看 API 和前端日志：

```bash
docker compose --env-file .env logs --tail=100 backend
docker compose --env-file .env logs --tail=100 frontend
```

## 7. 更新和备份

更新代码前先备份数据库：

```bash
mkdir -p backups
docker compose --env-file .env exec -T mariadb sh -c 'mariadb-dump -uroot -p"$MARIADB_ROOT_PASSWORD" "$MARIADB_DATABASE"' > "backups/glavk-$(date +%Y%m%d-%H%M%S).sql"
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
docker compose --env-file .env up -d --build
docker compose --env-file .env ps
```

## 8. 没有 HTTPS 的限制

没有域名和证书时，HTTP 不能防止主动中间人替换前端 JavaScript。项目的 RSA-OAEP + AES-GCM 只降低普通被动抓包直接得到密码的风险，不能替代 HTTPS。没有 HTTPS 时只建议在 localhost、可信内网或 VPN/Tailscale 中使用；公网使用必须在反向代理前配置 HTTPS。
