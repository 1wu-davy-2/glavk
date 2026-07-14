# glavk 凭据传输与网页截图优化设计

## 范围

本次变更包含三项：允许纯静态 Web 系统不填写用户名和密码；保存项目时由后端尝试抓取公开 URL 的网页截图作为卡片封面；在没有 HTTPS 的现实环境下增加应用层凭据加密，降低普通被动抓包直接得到密码的风险。

## 安全边界

没有域名和受信任证书时，HTTP 无法防御中间人读取或篡改 HTML/JavaScript。应用层加密只能保护被动抓包，不能阻止主动攻击者替换前端脚本。因此文档和部署说明必须明确：公网使用仍需 HTTPS；无 HTTPS 时应只在 localhost、可信内网或 VPN/Tailscale 内使用。

应用层加密不使用固定的前端秘钥。固定秘钥会随前端代码下发，无法形成安全边界。改为：

- 后端持有 RSA- OAEP 传输私钥，私钥来自 `TRANSPORT_PRIVATE_KEY_B64` 环境变量，生产环境禁止自动生成。
- 后端只公开 RSA 公钥。
- 前端每次页面会话用 WebCrypto 生成不可导出的临时 RSA-OAEP 私钥，私钥只存在内存，不写入 localStorage。
- 保存项目凭据时，前端用后端公钥封装随机 AES-GCM 密钥后发送加密 envelope；后端解密到内存，再用现有 Fernet 数据库密钥加密后落库。
- 查看或复制凭据时，请求带前端临时公钥；后端从数据库解密后使用前端公钥重新加密返回；前端仅在查看/复制动作中解密，完成后清理内存中的明文。
- 普通项目列表不返回用户名和密码明文，只返回 `has_credentials` 和掩码状态。

除凭据字段外，不把密码放入 URL、日志、localStorage、错误信息或截图请求。使用 CSP、禁止 framing、`nosniff`、严格 Referrer Policy 和私有缓存头减少浏览器攻击面。

## 可选凭据

`username` 和 `password` 都允许为空。两者都为空时项目标记为“无需登录”，卡片不显示凭据行；只填写其中一个也允许保存。数据库将 `password_ciphertext` 改为可空，历史加密数据保持兼容。

## 网页截图

保存或更新项目后，后端使用 Playwright Chromium 访问项目公开 URL，固定 1280x720 视口并截取首屏 PNG。截图浏览器不使用项目凭据，不自动登录目标站点。截图保存到 `SCREENSHOT_DIR`（Docker 中挂载到持久化数据卷），数据库只保存相对路径，卡片通过需要管理员 token 的 `/api/projects/{id}/screenshot` 读取。

截图是增强信息，不是保存成功的前置条件：目标站点超时、拒绝访问、无 Chromium 或命中安全策略时，项目仍然保存，卡片退回首字母图标。为降低 SSRF 风险，默认拒绝 localhost、私有网段、链路本地地址、保留地址和非 HTTP(S) URL；可信内网部署可显式设置 `SCREENSHOT_ALLOW_PRIVATE_NETWORKS=true`。

## API 变化

- `GET /api/security/transport-key` 返回后端传输公钥。
- `POST /api/projects` 接受可选 `credential_envelope`，不再要求明文用户名/密码。
- `PUT /api/projects/{id}` 接受可选 `credential_envelope`；没有 envelope 时保持已有凭据。
- `GET /api/projects` 和 `GET /api/projects/{id}` 返回 `has_credentials`、`has_screenshot`，不返回用户名和密码明文。
- `GET /api/projects/{id}/credential` 要求 `X-Client-Public-Key`，返回加密 envelope。
- `GET /api/projects/{id}/screenshot` 要求 bearer token，返回 PNG 或 404。

## 错误处理与测试

- envelope 缺字段、RSA 解密失败、AES-GCM 验证失败统一返回中文“凭据数据无效”，不回显密文。
- 截图失败只记录不包含 URL query 密钥的结构化警告，并把项目保持为可用状态。
- 后端测试覆盖空凭据、单字段凭据、加密 envelope 解密、响应 envelope、截图路径和 SSRF 拒绝。
- 前端测试覆盖纯静态项目提交、transport key 初始化、加密 payload 不含明文、凭据点击解密/复制、截图 blob 展示和截图缺失降级。
- 继续运行 pytest、Vitest、Vite build 和 smoke test；Docker CLI 若仍不可用则只记录限制。

