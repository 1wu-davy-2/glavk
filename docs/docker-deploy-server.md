# glavk 服务器 Docker 部署教程

本文按 Ubuntu 22.04/24.04 编写。默认端口为：前端 `6222`、API `6555`。前端 nginx 会在 Docker 内部代理 `/api`，后端默认只绑定服务器本机，远程用户只需要访问前端端口。

数据库开箱即用：SQLite 把整个库放在容器内的 `/app/data/glavk.sqlite3`，不需要另外安装或配置数据库服务，也没有账号密码要填。这个文件存在 `backend_data` 卷里，哪些操作安全、哪些会丢数据、怎么备份，见第 7 步。

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

服务器最终只保留并使用项目根目录的 `.env`，前后端不再分别配置。**数据库不需要任何配置**，保持模板里的默认值就行：

```dotenv
DATABASE_URL=sqlite:////app/data/glavk.sqlite3
```

注意是**四个斜杠**：`sqlite://` 后面跟的是容器内的绝对路径 `/app/data/...`。少写一个斜杠会变成相对路径，容器一重建数据就没了。

端口和管理员账号建议修改：

```dotenv
FRONTEND_PORT=6222
BACKEND_PORT=6555
ADMIN_USERNAME=admin
ADMIN_PASSWORD=修改为管理员密码
```

密码建议只使用字母、数字和 `._-@!`，避免在 `.env` 中使用未转义的空格、`#` 和换行。其余变量保持模板内容即可。前端通过 nginx 同源转发 `/api`，不需要填写服务器 IP 或 `VITE_API_BASE_URL`。

如果服务器只能用 `http://IP:6222` 访问（没有 HTTPS），还要把 `ALLOW_PLAINTEXT_CREDENTIALS` 设为 `true`，否则浏览器不提供 WebCrypto，登录页点登录就会报错，见第 8.1 节。

想改回外部 MySQL/MariaDB，把 `DATABASE_URL` 换成 `mysql+pymysql://账号:密码@主机:3306/glavk?charset=utf8mb4` 即可，代码和 compose 都不用改；密码里的 `@ : / ? #` 由后端自动做 URL 编码。

后端首次启动会把自动生成的 `AUTH_SECRET_KEY`、`CREDENTIAL_ENCRYPTION_KEY` 和 `TRANSPORT_PRIVATE_KEY_B64` 保存到 `backend_data` 卷。**这个卷现在还装着 SQLite 数据库本体**，所以不要删除它：删掉不仅历史项目密码无法解密、登录 token 失效，所有项目数据也会一起消失。

## 4. 防火墙

只开放前端端口。后端默认绑定服务器本机，不要对公网开放 `6555`：

```bash
sudo ufw allow OpenSSH
sudo ufw allow 6222/tcp
sudo ufw enable
sudo ufw status
```

## 5. 检查配置并启动

先让 Compose 展开变量，确认没有残留 `CHANGE-`：

```bash
docker compose config > /tmp/glavk-compose.yml
grep -E "BACKEND_BIND_ADDRESS|BACKEND_PORT|FRONTEND_PORT|DATABASE_URL" /tmp/glavk-compose.yml
```

重点确认 `DATABASE_URL` 展开后是 `sqlite:////app/data/glavk.sqlite3`（四个斜杠、绝对路径）。

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

数据库、截图和运行时密钥都在同一个卷里，备份这个卷就等于备份全部数据。先确认卷名：

```bash
docker volume ls | grep backend_data      # 默认是 glavk_backend_data
```

SQLite 写入时会产生 `glavk.sqlite3-wal` 和 `glavk.sqlite3-shm`，**必须和主文件一起打包**，所以停几秒后端再备份：

```bash
mkdir -p backups
docker compose stop backend
docker run --rm -v glavk_backend_data:/data -v "$PWD/backups:/backup" \
  alpine tar czf /backup/glavk-data-$(date +%Y%m%d-%H%M%S).tar.gz -C /data .
docker compose start backend
```

恢复：

```bash
docker compose down
docker run --rm -v glavk_backend_data:/data -v "$PWD/backups:/backup" \
  alpine sh -c 'find /data -mindepth 1 -delete && tar xzf /backup/glavk-data-20260921-120000.tar.gz -C /data'
docker compose up -d
```

注意：只恢复数据库文件而丢了 `runtime-secrets.env` 里的 `CREDENTIAL_ENCRYPTION_KEY`，已保存的项目密码就永远解不开了，所以务必整卷一起备份、一起恢复。

**日常操作里只有两条会丢数据**：`docker compose down -v`（`-v` 会连卷一起删）和 `docker volume rm <卷名>`。`docker compose up -d --build`、`restart`、`down`（不带 `-v`）都不会动数据。另外卷名带项目目录前缀，把仓库换到别的目录（比如 `glavk-dev`）会挂上一个全新的空卷，看起来就像数据被覆盖了——完整的说明和排查方法见 README 的「数据持久化」一节。

完全清空重来：

```bash
docker compose down
docker volume rm glavk_backend_data
docker compose up -d --build
```

更新：

```bash
git pull --ff-only
docker compose up -d --build
docker compose ps
```

## 8. 没有 HTTPS 的限制

没有域名和证书时，HTTP 不能防止主动中间人替换前端 JavaScript。项目的 RSA-OAEP + AES-GCM 只降低普通被动抓包直接得到密码的风险，不能替代 HTTPS。没有 HTTPS 时只建议在 localhost、可信内网或 VPN/Tailscale 中使用；公网使用必须在反向代理前配置 HTTPS。

### 8.1 纯 HTTP 访问必须开启 ALLOW_PLAINTEXT_CREDENTIALS

浏览器只在**安全上下文**（HTTPS、`localhost`、`127.0.0.1`）暴露 WebCrypto，也就是 `crypto.subtle`。用 `http://服务器IP:6222` 打开时 `crypto.subtle` 是 `undefined`，前端无法做任何加密，登录会直接失败（表现为 `Cannot read properties of undefined (reading 'importKey')`）。

为此后端提供一个显式开关，默认关闭：

```ini
ALLOW_PLAINTEXT_CREDENTIALS=true
```

开启后：

- 前端检测不到 `crypto.subtle` 时，登录、保存项目凭据、复制密码改为明文提交，功能全部可用；登录页底部会显示"明文传输 · 请在可信网络使用"。
- 只要浏览器能加密（HTTPS 或 localhost 访问），仍然优先走 RSA-OAEP + AES-GCM 加密通道，该开关不影响加密路径。
- 后端启动日志会打印一条 warning 提示当前处于明文模式。

安全代价：HTTP 链路上的登录密码和项目密码是明文，任何能被动抓包的人都能直接读到；同时 `Authorization` token 也在明文 HTTP 中传输，拿到即可访问全部数据。因此**只在自用、可信网络下开启**；公网可访问的部署请配置 HTTPS 并保持该项为 `false`。

没有 HTTPS 时前端的 `navigator.clipboard` 同样不可用，复制密码会自动退回旧的 `document.execCommand("copy")`，不需要额外配置。
