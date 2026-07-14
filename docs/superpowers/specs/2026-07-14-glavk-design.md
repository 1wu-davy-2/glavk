# glavk 网页系统管理平台设计规格

## 目标

新增独立目录 `glavk`，构建一个中文网页系统管理平台。管理员登录后可以以卡片方式浏览所有 Web 系统，录入访问地址、用户名、密码和补充信息，并快速打开目标系统或复制登录凭据。

## 体验与界面

采用 Stitch 共享项目的中文后台管理方向，以蓝白为主色，强调清晰的信息层级和高频操作效率。桌面端为 230px 左侧导航 + 内容区布局，首页顶部提供搜索、分类筛选、统计概览和“添加系统”操作，主体为三列响应式项目卡片。卡片显示系统图标、名称、地址、分类、用户名、掩码密码、启用状态、收藏状态和最近更新时间；眼睛按钮查看密码，复制按钮复制密码，打开按钮使用新标签页打开 URL。

添加和编辑共用右侧抽屉表单。手机端导航收缩为顶部导航，卡片变为单列，抽屉变为全屏表单。需要覆盖加载骨架、空状态、错误状态、保存成功、删除确认和复制成功等状态。按钮使用 lucide-react 图标并保留中文可读标签；所有表单控件要有可见 label 和键盘焦点样式。

## 后端架构

FastAPI 应用提供 `/api/health`、`/api/auth/login`、`/api/auth/me`、`/api/projects` 以及项目详情、凭据查看和删除接口。SQLAlchemy 连接 MariaDB 数据库 `glavk`，启动时创建表结构。单管理员账号由环境变量初始化到 `admin_users` 表，登录密码使用 PBKDF2-HMAC 哈希，不保存明文。

项目密码需要可被管理员取回，因此使用 Fernet 对称加密写入 `web_projects.password_ciphertext`。Fernet 密钥来自 `CREDENTIAL_ENCRYPTION_KEY` 环境变量。列表和普通详情只返回 `password_masked`，明确的凭据查看接口才解密返回密码，且始终要求有效 bearer token。

token 为服务端签名的 bearer token，包含管理员标识和过期时间，默认 TTL 30 天。前端把 `{accessToken, expiresAt, user}` 写入 localStorage；请求 401 时清理并返回登录页。生产环境必须设置随机 `AUTH_SECRET_KEY`、`CREDENTIAL_ENCRYPTION_KEY` 和管理员密码。

## 数据模型

### `admin_users`

- `id` UUID 主键
- `username` 唯一管理员名
- `password_hash`
- `is_active`
- `created_at`, `updated_at`

### `web_projects`

- `id` UUID 主键
- `name` 必填，最长 120 字符
- `url` 必填，必须为 `http://` 或 `https://`
- `category` 默认“未分类”
- `description`, `notes`
- `username`
- `password_ciphertext`
- `is_favorite`, `is_enabled`
- `sort_order`
- `created_at`, `updated_at`

## 安全与错误处理

- 所有项目接口和凭据查看接口要求 bearer token。
- 登录错误统一返回“用户名或密码错误”，不泄露账号是否存在。
- URL、名称、用户名和密码在后端再次校验，不能只依赖前端校验。
- 删除需要前端二次确认；后端删除不存在的 ID 返回 404。
- 密码不进入普通列表 JSON，不写入日志，不出现在错误信息中。
- CORS 只允许配置的前端来源；生产环境拒绝默认密钥。

## 测试策略

- 后端 pytest 覆盖密码哈希、登录成功/失败、token 过期、项目校验、加密存储、列表过滤、创建、更新、查看凭据和删除。
- 前端 Vitest + Testing Library 覆盖登录提交、session 30 天保存、401 清理、项目卡片、搜索筛选、抽屉保存、密码查看/复制和删除确认。
- 交付前运行 `pytest -q`、`npm test`、`npm run build`，并使用浏览器完成登录和项目管理主流程验证。

## 部署

Docker Compose 提供三个服务：

- `frontend`: nginx，宿主机 `6222`，容器 `80`
- `backend`: uvicorn，宿主机 `6555`，容器 `8000`
- `mariadb`: MariaDB 11，宿主机 `3307`，容器 `3306`

nginx 将 `/api` 反向代理到 `backend:8000`，前端以同源方式访问 API。默认数据库名为 `glavk`。

