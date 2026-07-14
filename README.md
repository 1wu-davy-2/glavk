# glavk

glavk 是一个中文网页系统管理后台，用卡片统一管理多个 Web 系统的访问地址、登录用户名和密码。首版采用单管理员登录，登录 token 默认有效 30 天。

## 技术栈

- 前端：React 18、TypeScript、Vite、lucide-react
- 后端：Python 3.12、FastAPI、SQLAlchemy
- 数据库：MariaDB 11，数据库名 `glavk`
- 部署：Docker Compose + nginx

## Docker 部署

1. 复制环境变量文件并修改其中的数据库密码、管理员密码和两个随机密钥：

```powershell
Copy-Item .env.example .env
```

`AUTH_SECRET_KEY` 至少 32 个字符。`CREDENTIAL_ENCRYPTION_KEY` 必须是 Fernet 密钥，可以使用下面的命令生成：

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

2. 启动全部服务：

```powershell
docker compose --env-file .env up -d --build
```

3. 访问：

- 前端：`http://localhost:6222`
- 后端健康检查：`http://localhost:6555/api/health`
- MariaDB：`localhost:3307`

首次启动会按照 `ADMIN_USERNAME` 和 `ADMIN_PASSWORD` 自动创建管理员账号。修改 `.env` 后需要重新创建或重启 backend 容器；已经创建的管理员不会被覆盖。

## 固定端口

| 服务 | 宿主机端口 | 容器端口 |
|---|---:|---:|
| 前端 nginx | 6222 | 80 |
| FastAPI 后端 | 6555 | 8000 |
| MariaDB | 3307 | 3306 |

端口可以通过 `.env` 覆盖，但默认值已经按本项目固定下来。前端 nginx 会把 `/api` 请求转发到 Compose 内部的 `backend:8000`。

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
- 查看或复制密码需要有效 token。
- 生产环境不要使用 Compose 默认密钥和默认密码。
- 数据库备份需要与 MariaDB 数据卷同时保护；项目密码密文依赖 `CREDENTIAL_ENCRYPTION_KEY`，密钥丢失后无法解密历史凭据。

