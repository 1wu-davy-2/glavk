# glavk

glavk 是一个中文网页系统管理后台，用卡片统一管理多个 Web 系统的访问地址、登录用户名和密码。首版采用单管理员登录，登录 token 默认有效 30 天。用户名和密码均可留空，适合静态网页或公开系统。

## 技术栈

- 前端：React 18、TypeScript、Vite、lucide-react
- 后端：Python 3.12、FastAPI、SQLAlchemy
- 数据库：MariaDB 11，数据库名 `glavk`
- 部署：Docker Compose + nginx

## Docker 部署

服务器部署请直接使用 [服务器 Docker 部署教程](docs/docker-deploy-server.md) 和 `glavk.env.example`。这是一个可直接上传的可见文件，上传后在服务器目录中复制为 `.env`。只需要修改端口、数据库账号密码和管理员账号密码；后端会在首次启动时自动生成并持久化三项加密密钥。

前后端共用项目根目录下的唯一 `.env`。Compose 会把它用于 MariaDB、FastAPI 和前端服务端口，不需要分别准备前后端配置文件；前端 API 使用同源地址，不需要构建期 API 配置：

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
| MariaDB | 3307 | 3306 |

端口可以通过 `.env` 覆盖，但默认值已经按本项目固定下来。前端 nginx 会把 `/api` 请求转发到 Compose 内部的 `backend:8000`。如需从服务器本机调试 API，可访问 `http://127.0.0.1:6555`；不建议把后端端口绑定到公网网卡。

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

截图功能在保存或更新项目后尝试访问公开的 HTTP(S) 地址，固定使用 1280x720 首屏 PNG。截图不使用项目登录凭据，失败不会阻止项目保存，卡片会退回首字母图标。默认拒绝 localhost、私有网段、链路本地地址、保留地址和非 HTTP(S) 地址；只有在可信内网中才可以显式设置 `SCREENSHOT_ALLOW_PRIVATE_NETWORKS=true`。

如果数据库是在旧版本中创建的，启动时会自动补齐 `screenshot_path` 列；也可以手动执行 `backend/sql/002_add_screenshot_path.sql`。

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
- 登录、保存和复制密码使用 RSA-OAEP + AES-GCM 应用层加密；复制动作才在浏览器内存中解密，普通列表和 localStorage 不保存项目密码。
- 查看或复制密码需要有效 token；截图接口也需要有效 token。
- 生产环境不要使用 Compose 默认密钥和默认密码。
- 数据库备份需要与 MariaDB 数据卷同时保护；项目密码密文依赖 `CREDENTIAL_ENCRYPTION_KEY`，密钥丢失后无法解密历史凭据。

## 没有 HTTPS 时的边界

没有域名和证书时，HTTP 无法防御主动中间人替换前端脚本，也无法保证公网链路的完整性。应用层加密只能降低普通被动抓包直接得到密码的风险，不能替代 HTTPS。无 HTTPS 时请只在 localhost、可信内网或 VPN/Tailscale 内使用；公网部署必须在前置反向代理配置 HTTPS。
