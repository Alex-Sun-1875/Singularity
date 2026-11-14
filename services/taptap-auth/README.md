# TapTap 小游戏登录服务

**历史实现，当前小游戏已停用（2026-11-13）。** 用户明确选择直接使用 TapTap 小游戏平台账号能力，当前客户端和构建不再调用本服务、不需要 `serviceUrl` 或服务器 Secret。以下自建登录部署说明仅作历史保留，不是当前接入步骤；当前方案见 [小游戏发布说明](../../src/cocos/release/README.md)。

适用于当前 Cocos 小游戏「剑与火：破晓之战」，MiniApp ID `tapmcddcmbhf5lxqng`。使用 Node 22.13+（22.x）内置 HTTP、Fetch、Crypto、SQLite，无需安装 npm 依赖。SQLite 在 Node 22 中仍标记 experimental；本地验证版本为 22.22.x。Docker 固定 22.22.0，生产维护时应跟进 22.x 安全更新。

客户端 `tap.login` → 本服务 → 官方 `code2Session` → `openid` → 随机自定义会话。没有合适的现成项目登录服务，因此这里只编写官方 API 适配与会话路由，复用 Node 的网络、随机数和 SQLite 能力。

## 本地运行

将 `.env.example` 复制为 `.env`，**只在服务器本地**填入小游戏后台的 Secret。不要把 Secret 发到聊天、提交仓库或填入 Cocos 配置。小游戏 Secret 不是游戏 ID、MiniApp ID 或普通 TapSDK Client Secret。

```powershell
cd F:\workspace\Singularity\services\taptap-auth
Copy-Item .env.example .env
# 在本地编辑 .env 填入 TAPTAP_MINIAPP_SECRET
node --env-file=.env server.mjs
```

默认监听 `127.0.0.1:8787`，健康检查 `GET /healthz`。缺少密钥会拒绝启动，不存在模拟登录模式。`npm test` 使用隔离的官方响应 fixture，仅验证代码行为，不访问真实 TapTap。

## 部署

选用一台能直连 `cloud-miniapp.tapapis.cn:443` 的服务器或支持持久卷的容器服务。当前实现采用**单实例 + 持久化 SQLite**，不适合无持久磁盘、随时销毁实例的云函数；多实例需更换为共享数据库。

1. 配置 `.env` 或托管平台的密钥环境变量；数据目录仅允许服务账号读取。持久保存 `SESSION_DB_PATH` 指向的 SQLite 文件及 WAL 文件。自定义 token 仅保存 SHA-256 摘要，默认有效 24 小时；过期记录在启动时及每分钟清理。
2. 在已有服务器上按上述 Node 命令运行并使用服务管理器守护；或构建下面的容器。服务本身监听 HTTP，外层必须有 HTTPS 反向代理/托管入口，使用有效证书并禁止公网访问内部 HTTP 端口。
3. 使用已备案的 HTTPS 域名作为入口，例如 `https://你的登录域名`。代理转发 `/auth/*` 和 `/healthz`，限制请求体 4KB、超时 15 秒，可在入口按 IP 限流。访问日志不得记录 Authorization、请求体或上游完整 URL。
4. 在 TapTap 后台「小游戏管理 → 开放能力 → 服务器域名」添加该 **request 域名**。遵循平台 HTTPS、备案及域名要求，不配置 IP、localhost 或自定义端口。
5. 将公开地址填入 `src/cocos/release/taptap-auth.json` 的 `serviceUrl`，不带 `/auth/taptap` 后缀。客户端 MiniApp ID 统一读取 `taptap-project.json`，必须与服务器环境变量一致。脚本将这些公开值生成到 `TapAuthConfig.ts`。
6. 在仓库根目录运行 `npm run build:tap`，版本读取根目录 `package.json`，再上传并进行 TapTap 真机扫码验收。未填服务地址时正式构建会拒绝；`build:tap:audit` 仅用于本地检查，不能上传代替正式包。

Docker（已有直连 Docker 环境时执行；本轮未下载镜像或运行 Docker）：

```powershell
docker build -t singularity-taptap-auth .
docker volume create singularity-taptap-auth-data
docker run -d --name singularity-taptap-auth --restart unless-stopped --env-file .env -e HOST=0.0.0.0 -e SESSION_DB_PATH=/app/data/sessions.sqlite -p 127.0.0.1:8787:8787 -v singularity-taptap-auth-data:/app/data singularity-taptap-auth
```

## 接口与运行边界

- `POST /auth/taptap`：JSON `{ "miniAppId": "tapmcddcmbhf5lxqng", "code": "tap.login 返回的临时凭证" }`。服务器校验项目标识并向官方交换身份。返回 `{token, expiresAt, user:{openid, unionid?}}`，`expiresAt` 是毫秒时间戳。
- `GET /auth/session`：`Authorization: Bearer <token>`，验证自定义会话并返回相同结构；过期或未知 token 返回 401。
- `DELETE /auth/session`：同样的授权头，撤销自定义会话；客户端当前不提供账号管理/退出入口。
- 所有认证响应 `Cache-Control: no-store`。服务限制每分钟 120 次官方换码及 600 次业务请求；规模扩大时应调整入口策略与共享存储。
- `session_key` 不传给客户端，也不持久化。当前游戏没有使用需要解密的用户资料，因此取得身份后立即丢弃。无头像/昵称授权、云存档、支付接入。
- 客户端 token 只保存在运行内存；重新打开游戏重新登录。返回前台先执行 `tap.checkSession`，再校验自定义会话；平台状态失效或自定义会话过期会重新换码。网络失败显示重试，期间暂停玩法并保留本地存档。
- 浏览器预览显式标记 `preview`，不伪装成已完成 TapTap 登录。要求登录的小游戏构建缺 API、无 code、服务失败或配置为空均不能进入游戏。独立的 `npm run pack:taptap:guest` 是用户授权的游客测试例外，明确标记 `guest`、跳过业务登录，仅使用现有本机存档，不代表已验证 TapTap 身份。登录成功不改变既有本地存档归属，不提供跨设备或按账号云存档。

## 还需完成的外部配置

当前没有部署地址或真实服务器密钥。开发者需准备服务器/容器环境及备案域名，在服务器密钥配置中填入 Secret，再填写公开 `serviceUrl` 和平台请求域名。上线前完成隐私声明，说明服务处理 openid/unionid、自定义登录会话及其用途/保存期限。

真机需验证：首次登录、断网及重试、切后台恢复、会话过期重登、杀进程重开、平台账号切换及本地存档保持。浏览器和响应 fixture 不能替代平台验收。

官方依据：[登录流程](https://developer.taptap.cn/minigameapidoc/dev/tutorial/open-capabilities/login-management/)、[tap.login](https://developer.taptap.cn/minigameapidoc/dev/api/open-api/login/tap.login/)、[tap.checkSession](https://developer.taptap.cn/minigameapidoc/dev/api/open-api/login/tap.checkSession/)、[code2Session](https://developer.taptap.cn/minigameapidoc/dev/server/login/code2Session/)、[网络域名规则](https://developer.taptap.cn/minigameapidoc/dev/tutorial/basic/network/)、[Node SQLite](https://nodejs.org/download/release/v22.23.0/docs/api/sqlite.html)。
