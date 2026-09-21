# glavk

glavk 是一个中文网页系统管理后台，用卡片统一管理多个 Web 系统的访问地址、登录用户名和密码。首版采用单管理员登录，登录 token 默认有效 30 天。用户名和密码均可留空，适合静态网页或公开系统。

## 技术栈

- 前端：React 18、TypeScript、Vite、lucide-react
- 后端：Python 3.12、FastAPI、SQLAlchemy
- 数据库：SQLite，整个库就是容器里的一个文件 `/app/data/glavk.sqlite3`
- 部署：Docker Compose + nginx

## Docker 部署

服务器部署请直接使用 [服务器 Docker 部署教程](docs/docker-deploy-server.md) 和 `glavk.env.example`。这是一个可直接上传的可见文件，上传后在服务器目录中复制为 `.env`。只需要修改端口和管理员账号密码；后端会在首次启动时自动生成并持久化三项加密密钥。纯 HTTP（没有 HTTPS）部署还要把 `ALLOW_PLAINTEXT_CREDENTIALS` 设为 `true`，否则登录会失败，见下文"没有 HTTPS 时的边界"。

数据库开箱即用，**不需要安装、不需要建库建账号**：SQLite 把整个库放在容器内的 `/app/data/glavk.sqlite3`，这个目录挂在持久卷上。首次启动会自动建表并创建管理员账号。数据怎么保存、什么操作会丢，见[数据持久化](#数据持久化哪些操作安全哪些会覆盖数据)。

前后端共用项目根目录下的唯一 `.env`。Compose 会把它用于 FastAPI 和前端服务端口，不需要分别准备前后端配置文件；前端 API 使用同源地址，不需要构建期 API 配置：

```powershell
Copy-Item glavk.env.example .env
docker compose up -d --build
```

生产镜像中的前端使用同源 `/api`，由 nginx 转发到 Compose 内部的 `backend:8000`。后端宿主机端口默认只绑定 `127.0.0.1`，远程用户只需要访问前端端口；这样无需填写服务器 IP，也减少了 HTTP 下暴露 API 的风险。

## 固定端口

| 服务 | 宿主机端口 | 容器端口 |
|---|---:|---:|
| 前端 nginx | 6222 | 80 |
| FastAPI 后端（仅服务器本机） | 6555 | 8000 |

端口可以通过 `.env` 覆盖，但默认值已经按本项目固定下来。前端 nginx 会把 `/api` 请求转发到 Compose 内部的 `backend:8000`。如需从服务器本机调试 API，可访问 `http://127.0.0.1:6555`；不建议把后端端口绑定到公网网卡。

## 数据持久化：哪些操作安全，哪些会覆盖数据

SQLite 版本把整个数据库放在一个文件里：

```text
容器内路径：/app/data/glavk.sqlite3
宿主机卷名：<项目目录名>_backend_data
```

项目目录叫 `glavk` 时卷名就是 `glavk_backend_data`，用 `docker volume ls | grep backend_data` 确认实际名字。同一目录下还有截图（`/app/data/screenshots`）和运行时密钥（`/app/data/runtime-secrets.env`），三者一起存在这个卷里。

数据在**卷**里、不在镜像里，所以日常操作是安全的：

| 操作 | 数据 | 说明 |
|---|---|---|
| `docker compose up -d --build` | ✅ 保留 | 日常更新代码、重建镜像用这条 |
| `docker compose restart` / `stop` / `start` | ✅ 保留 | |
| `git pull` 后重新构建 | ✅ 保留 | 卷不受影响 |
| `docker compose down` | ✅ 保留 | 不加 `-v` 就不会删卷 |
| `docker compose down -v` | ❌ **全丢** | `-v` 会连命名卷一起删 |
| `docker volume rm <卷名>` | ❌ **全丢** | |
| `docker volume prune` | ❌ **全丢** | 卷没被运行中的容器占用时会被清掉 |

### 三个最容易"数据不见了"的坑

**1. 换了项目目录，就等于换了卷。** 卷名带项目目录前缀。仓库从 `/root/glavk` 换到 `/root/glavk-dev`，Compose 会建一个全新的空卷 `glavk-dev_backend_data`，打开的是空库——看着像数据被覆盖了，其实旧数据还在原来那个卷里。要么保持目录名不变，要么固定项目名：

```bash
COMPOSE_PROJECT_NAME=glavk docker compose up -d --build
```

**2. 改了 `DATABASE_URL` 的路径。** 指向 `/app/data/` 以外的路径就是换了一个新库。确认当前用的是哪个：

```bash
docker compose exec backend printenv DATABASE_URL
```

**3. 把持久卷改成了 bind mount。** 如果 `docker-compose.yml` 里的 `backend_data:/app/data` 被改成 `./data:/app/data`，而宿主机 `./data` 是空的，容器里就是空的。这个版本保持了命名卷，不用改。

### 备份

SQLite 写入时会产生 `glavk.sqlite3-wal` 和 `glavk.sqlite3-shm` 两个附属文件，**必须和主文件在同一个目录**，单独拷 `.sqlite3` 可能拿到不完整的数据。最稳的做法是停几秒后端再打包：

```bash
cd /root/glavk
mkdir -p backups
docker compose stop backend
docker run --rm -v glavk_backend_data:/data -v "$PWD/backups:/backup" \
  alpine tar czf /backup/glavk-data-$(date +%Y%m%d-%H%M%S).tar.gz -C /data .
docker compose start backend
```

这个包里同时包含数据库、截图和运行时密钥。恢复时三者要配套使用——项目密码的密文依赖 `runtime-secrets.env` 里的 `CREDENTIAL_ENCRYPTION_KEY`，只恢复数据库而丢了密钥，历史密码就解不开了。

### 恢复

```bash
cd /root/glavk
docker compose down
docker run --rm -v glavk_backend_data:/data -v "$PWD/backups:/backup" \
  alpine sh -c 'find /data -mindepth 1 -delete && tar xzf /backup/glavk-data-20260921-120000.tar.gz -C /data'
docker compose up -d
```

把 `glavk-data-20260921-120000.tar.gz` 换成你实际要恢复的备份文件名。

### 清空重来

```bash
docker compose down
docker volume rm glavk_backend_data
docker compose up -d --build
```

重建后自动建表，并按 `.env` 里的 `ADMIN_USERNAME` / `ADMIN_PASSWORD`(`_HASH`) 重新创建管理员账号。

## 本地开发

后端：

```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn app.main:app --app-dir backend --reload --port 6555
```

前端：

```powershell
Set-Location frontend
npm install
npm run dev
```

Vite 前端默认使用 `6222`，并将 `/api` 代理到 `http://127.0.0.1:6555`。本地开发没有设置 `CREDENTIAL_ENCRYPTION_KEY` 时，会从开发用 `AUTH_SECRET_KEY` 派生稳定密钥；生产环境必须显式设置独立 Fernet 密钥。

本地不设置 `DATABASE_URL` 时同样走 SQLite，默认落在工作目录下的 `./data/glavk.sqlite3`。目录会自动创建，表在启动时自动建好；想从头来过直接删掉这个文件即可（连同同目录的 `-wal` / `-shm`）。该文件已被 `.gitignore` 的 `*.sqlite3` 排除，不会误提交。

截图功能在保存或更新项目后尝试访问公开的 HTTP(S) 地址，固定使用 1280x720 首屏 PNG。截图不使用项目登录凭据，失败不会阻止项目保存，卡片会退回首字母图标。默认拒绝 localhost、私有网段、链路本地地址、保留地址和非 HTTP(S) 地址；只有在可信内网中才可以显式设置 `SCREENSHOT_ALLOW_PRIVATE_NETWORKS=true`。

启动时会执行 `Base.metadata.create_all` 建表，缺列的老库也会自动补齐，不需要手工跑 SQL。

## 验证命令

```powershell
python -m pytest backend/tests -q
Set-Location frontend
npm test
npm run build
Set-Location ..
docker compose config
```

## 安全说明

- 管理员登录密码只保存 PBKDF2-HMAC 哈希。
- Web 系统密码使用 Fernet 加密保存，普通项目列表不会返回明文密码。
- 登录、保存和复制密码使用 RSA-OAEP + AES-GCM 应用层加密；复制动作才在浏览器内存中解密，普通列表和 localStorage 不保存项目密码。只有显式设置 `ALLOW_PLAINTEXT_CREDENTIALS=true` 且浏览器无 WebCrypto 时才退回明文传输。
- 查看或复制密码需要有效 token；截图接口也需要有效 token。
- 生产环境不要使用 Compose 默认密钥和默认密码。
- 数据库、截图和运行时密钥都在同一个 Docker 卷里，备份和恢复必须整卷一起做；项目密码密文依赖 `CREDENTIAL_ENCRYPTION_KEY`，密钥丢失后无法解密历史凭据。

## 没有 HTTPS 时的边界

没有域名和证书时，HTTP 无法防御主动中间人替换前端脚本，也无法保证公网链路的完整性。应用层加密只能降低普通被动抓包直接得到密码的风险，不能替代 HTTPS。无 HTTPS 时请只在 localhost、可信内网或 VPN/Tailscale 内使用；公网部署必须在前置反向代理配置 HTTPS。

浏览器只在安全上下文（HTTPS、`localhost`、`127.0.0.1`）暴露 WebCrypto，所以用 `http://服务器IP:6222` 访问时前端拿不到 `crypto.subtle`，无法加密凭据，登录会失败。纯 HTTP 部署需要在 `.env` 中显式开启明文通道：

```ini
ALLOW_PLAINTEXT_CREDENTIALS=true
```

开启后前端在没有 `crypto.subtle` 时退回明文提交，功能完整可用；能加密时（HTTPS 或 localhost）仍然优先走加密通道。代价是 HTTP 链路上的密码和 token 都是明文，请只在自用、可信网络下开启，详细说明见[部署教程第 8 节](docs/docker-deploy-server.md)。
