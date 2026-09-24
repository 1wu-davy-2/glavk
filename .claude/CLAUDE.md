# 项目级 AI 协作规范

## 1. 最高优先级硬规则（必须置顶）

- 严禁 AI 署名：commit / PR / 代码注释 / 文档中绝对禁止出现 `Co-Authored-By: Claude`、
  `Generated with Claude Code` 及一切 AI 署名。GitHub 会据此把 AI 计入 Contributors。
- 隐私红线：严禁把真实密钥、凭据、内网地址写进代码、日志、报错、commit、测试快照。
  - 禁止回显 `.env` 实际值，以及 `AUTH_SECRET_KEY` / `CREDENTIAL_ENCRYPTION_KEY` /
    `TRANSPORT_PRIVATE_KEY_B64` / `ADMIN_PASSWORD` 的任何取值；引用一律用 `<YOUR_API_KEY>` 占位。
  - 禁止读取或打印 `data/runtime-secrets.env`、`data/glavk.sqlite3`、`data/screenshots/`
    （截图含真实系统页面）。
  - 外部地址只保留 `scheme://host`，不写完整带凭据 URL。
- 严禁在日志或异常里回显项目密码明文；`ProjectRead` 只允许 `password_masked` + `has_credentials`。

## 2. 测试与资源限制（解决跑测试卡死）

- 严禁裸跑测试，必须限制资源：
  - 后端：`python -m pytest backend/tests -q`（串行，不要加 `-n`）
  - 前端：`npm test -- --maxWorkers=2 --no-file-parallelism --bail=1`
- Playwright / 截图测试是 CPU 大户（`screenshot_service.py` 会拉起 Chromium）：
  `test_screenshot_service.py` 及截图相关用例单独跑，不要混进全量套件。
- 强制子代理机制：所有测试必须交给独立 sub-agent 执行。主对话只接收
  「失败文件名 + 行号 + 错误类型」三要素，禁止把完整日志、堆栈、pytest 收集树拉回主对话。
- 单次测试运行超过 120s 未结束就中断，先定位再重跑。

## 3. 架构与语义约束

- 凭据传输是双通道：优先 `credential_envelope`（RSA-OAEP + AES-GCM），仅当
  `ALLOW_PLAINTEXT_CREDENTIALS=true` 才接受 `credential_plaintext`。优先级只由
  `api/credentials.py::resolve_credentials` 决定，不要在路由里另写判断。
- `credential_envelope` / `credential_plaintext` 不得落库，持久化前必须 pop 掉。
- 语义不变式：凭据字段「缺省 = 本次不改动」，「显式传 null = 清空」，判别依据是
  `model_fields_set`（见 `services/projects.py::update`）。改这条前先看
  `frontend/src/api/client.ts::credentialFields`。
- 密码只存 Fernet 密文；读取走独立的 `/api/projects/{id}/credential` 认证接口，
  列表接口永不返回明文。
- URL 必须是 `http`/`https` 且有 netloc（`schemas.py` 的 validator），前后端各校验一次。
- SQLite 是唯一数据库。容器内路径必须四斜杠 `sqlite:////app/data/glavk.sqlite3`；
  三斜杠会落到容器可写层，容器重建即丢。
- `Settings` 是 frozen dataclass，只在构造时读环境变量；生产必填校验集中在
  `validate_production_security()`，新增生产必填项加在那里。
- `create_app()` 支持注入 `settings` / `session_factory` / `screenshot_service`，
  测试必须走注入，不要打真实 DB 或真实网络。
- 截图有 SSRF 防护：默认拒绝 localhost、私有网段、链路本地与保留地址，只有
  `SCREENSHOT_ALLOW_PRIVATE_NETWORKS=true` 才放行。不要为了跑通测试放宽默认值。
- 前端 API 同源（`VITE_API_BASE_URL ?? ""`），由 nginx 把 `/api` 转发到 `backend:8000`；
  不要引入构建期 API 地址。

## 4. Git 与构建交付

- 提交范围严格遵守当轮指令，不夹带无关文件。
- 不提交测试文件（`test_*.py`、`*.test.ts(x)`、`tests/`），除非当轮明确要求。
- 不提交 `.env`、`data/`、`*.sqlite3`、截图；这些已在 `.gitignore`，不要用 `-f` 绕过。
- 交付前验证：`python -m pytest backend/tests -q` + `npm test` + `npm run build` +
  `docker compose config`。
- 端口固定：前端 6222、后端 6555（仅绑 `127.0.0.1`）。改端口要同步 `.env` 与 README。

## 5. 执行流程约定

- 按里程碑推进，每完成一个阶段停下等确认。
- 改代码前先列出要改的文件清单并说明理由，等确认后再动手。
- 上下文到 40% 主动 `/compact`，丢弃测试日志与堆栈。
- 探测代码优先 Glob/Grep 抽样，禁止全量读取 `node_modules/`、`dist/`、`.git/`。
- 面向用户的说明与文档用中文。
