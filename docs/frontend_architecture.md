# 前端架构说明（阶段一）

> 本文档由 ZCode 编写，基于它实际写下的代码；目的是让你**能读懂、能维护、能解释**，而不是教你写 React。
> 重点在「架构、数据流、与后端的交互」，React 语法细节留给你以后按需补。
>
> 对应 PRD：[v1_prd.md](v1_prd.md) §6（页面清单）、§5（API 草案）、§3 的 F11–F16 / F21。

---

## 0. 一句话概括

前端是一个 **单页应用（SPA）**：一个 `index.html`，所有页面由 JavaScript 按 URL 动态渲染，和后端之间**只通过 HTTP JSON** 通信（外加阶段 F 要加的 SSE）。

技术栈（与 README 技术栈表一致）：

| 用途 | 选型 |
| --- | --- |
| 框架 | React 19 + TypeScript |
| 构建工具 | Vite 8 |
| UI 组件库 | Ant Design 6（+ `@ant-design/icons`） |
| 路由 | react-router-dom 7 |
| Markdown | marked 18 + DOMPurify 3 |

**没有引入**：Redux、Next.js、SSR、axios（用的是浏览器原生 `fetch`）。

---

## 1. 目录与文件职责

```text
frontend/
├── vite.config.ts          开发服务器配置：把 /api 转发给后端
├── index.html              唯一一个 HTML 文件，只含一个 <div id="root">
└── src/
    ├── main.tsx            入口：四层"包裹"
    ├── App.tsx             路由表
    ├── index.css           全局重置 + Markdown 排版
    │
    ├── types/api.ts        后端返回结构的 TypeScript 类型（纯类型，无运行时代码）
    │
    ├── api/                ★ 所有网络请求都在这层
    │   ├── client.ts       fetch 的统一封装（唯一直接调用 fetch 的地方）
    │   ├── auth.ts         注册 / 登录 / 取当前用户
    │   └── conversations.ts 会话 CRUD / 消息历史 / 发消息
    │
    ├── store/
    │   └── AuthContext.tsx ★ 全局登录态（token + 当前用户）
    │
    ├── pages/
    │   ├── LoginPage.tsx   登录 / 注册页
    │   └── ChatPage.tsx    ★ 聊天主页（唯一持有业务状态的页面）
    │
    └── components/
        ├── RequireAuth.tsx     路由守卫
        ├── ConversationList.tsx 左侧会话列表
        ├── MessageList.tsx      右侧消息流
        ├── MessageInput.tsx     输入框 + 发送
        └── Markdown.tsx         Markdown → 安全 HTML
```

**分层思路和后端是一致的**：`pages/components`（界面）→ `api/`（网络）→ 后端。界面组件不直接写 `fetch`。

---

## 2. 逐文件说明

### `vite.config.ts` —— 为什么不需要 CORS

```ts
server: {
  proxy: {
    '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
  },
},
```

开发时前端在 `:5173`、后端在 `:8000`，**如果前端直接请求 8000 就是跨域**，浏览器会拦。

但这里前端始终只请求**自己这个域名**（`localhost:5173/api/...`），由 Vite 开发服务器在背后转发给 8000。浏览器眼里这是同源请求，**所以整个项目不需要 CORS 中间件**。

生产环境由 **Nginx** 做同样的事（`/api` → 后端容器）。所以前端代码里始终写相对路径 `/api/v1/...`，**开发和生产不用区分环境**。

### `src/main.tsx` —— 四层包裹

```tsx
<ConfigProvider locale={zhCN}>      {/* AntD 全局配置（中文语言包） */}
  <BrowserRouter>                   {/* 路由：管 URL 和页面的对应关系 */}
    <AuthProvider>                  {/* 全局登录态 */}
      <App />                       {/* 路由表 */}
    </AuthProvider>
  </BrowserRouter>
</ConfigProvider>
```

从外到内各管一件事。**顺序有意义**：`AuthProvider` 必须在路由里面，因为路由守卫要读登录态。

### `src/App.tsx` —— 路由表

| 路径 | 页面 | 说明 |
| --- | --- | --- |
| `/login` | LoginPage | 免登录 |
| `/chat` | ChatPage | 需要登录 |
| `/chat/:conversationId` | ChatPage | 需要登录，定位到指定会话 |
| `*` | — | 一律重定向到 `/chat` |

`/chat` 和 `/chat/:conversationId` 用的是同一个组件 —— 组件内部通过 URL 参数决定显示哪个会话。这样"切换会话"就变成了**改 URL**，浏览器的前进/后退天然可用。

### `src/types/api.ts` —— 只写用得到的字段

后端返回的字段比这里多（比如 `user_id`、`origin`），前端只声明**真正会读的**。这是刻意和后端 schema 的"白名单"思路保持一致：后端加了新字段，不会悄悄影响前端。

⚠️ 注意 `AuthResponse` **不是信封**（没有 `code`/`data`），因为后端的注册/登录接口刻意不用统一响应格式（原因见 PRD §5.2 的例外说明）。

### `src/api/client.ts` —— 整个前端只有一个地方调 `fetch` ★

它负责四件事：

1. **统一拼前缀** `/api/v1`（配合 Vite 代理，不写完整域名）
2. **自动带 token**：有 token 就加 `Authorization: Bearer <token>`
3. **自动拆信封**：响应是 `{code, message, data}` 就把 `data` 交给调用方
4. **统一处理 401**：清 token、跳登录页

第 3 点的判断逻辑：

```ts
if (json && 'code' in json && 'data' in json) return json.data   // 信封接口
return json                                                       // 扁平接口（登录/注册）
```

第 4 点的价值：**业务代码里永远不会出现"如果 401 就跳登录"这种判断**。任何接口返回 401，`client.ts` 一处收口处理掉。

### `src/api/auth.ts` / `conversations.ts` —— 后端接口的一一映射

薄薄一层，每个函数对应一个后端端点，没有业务逻辑。**好处是"前端调了哪些接口"一眼可见**，接口变了只改这两个文件。

### `src/store/AuthContext.tsx` —— 登录态 ★

解决的问题：**"当前用户是谁"要被多个地方读到**（顶栏显示昵称、路由守卫判断有没有登录）。

用 React 自带的 Context 实现：

- `user` / `loading` / `login` / `register` / `logout` 五个东西
- 任何组件 `const { user } = useAuth()` 就能拿到，不用一层层传 props

**关键的一段**（刷新页面不掉登录）：

```tsx
useEffect(() => {
  if (!getToken()) { setLoading(false); return }
  authApi.me().then(setUser).catch(() => clearToken()).finally(() => setLoading(false))
}, [])
```

刷新页面时 localStorage 里的 token 还在，但**它可能已经过期或无效**。所以拿它换一次 `/auth/me`：成功才认为"已登录"，失败就清掉。

`loading` 这个状态也是为此存在：在 `me()` 返回之前，"有没有登录"是未知的。

### `src/pages/ChatPage.tsx` —— 唯一持有业务状态的页面 ★

它管四份状态：

| 状态 | 含义 |
| --- | --- |
| `conversations` | 左侧列表 |
| `messages` | 当前会话的消息 |
| `sending` | 是否正在等回答（用来禁用输入框和发送按钮） |
| `streamingText` | 正在生成中的回答文本（非 null 表示模型正在回答） |

**两个 `useEffect` 分别负责**：

1. 进页面时拉会话列表；URL 里没指定会话就自动跳到第一个
2. `currentId` 变化时拉该会话的消息历史 —— **依赖数组是 `[currentId]`，所以切换会话会自动重新拉**

**发消息 `handleSend` 的三个细节**：

- **乐观显示**：先把用户这句话插进界面（用负 id 当 React 的 key），不用等后端往返
- **`onDelta` 回调**：交给 `sendMessage` 调用，每来一段文本就往 `streamingText` 上加
- **失败时不清掉用户消息**：因为后端**先存用户消息再调模型**，所以那句话确实已经落库了，保留它是对的

### `src/components/Markdown.tsx` —— F21

```tsx
const html = DOMPurify.sanitize(marked.parse(text) as string)
return <div className="markdown-body" dangerouslySetInnerHTML={{ __html: html }} />
```

两步都不能省：

1. `marked` 把 Markdown 转成 HTML（模型回答里带 `**加粗**`、列表、代码块）
2. `DOMPurify.sanitize` 洗掉危险标签和属性

**第 2 步是安全措施，不是可选优化**：这段内容来自大模型（阶段二还会来自知识库文档），属于不可信输入。把未消毒的 HTML 交给 `dangerouslySetInnerHTML` 是最典型的 XSS 入口。相关约束写在 PRD §8.2 第 16 项。

---

## 3. 与后端的交互（重点）

### 3.1 请求的完整物理路径

```text
组件 (ChatPage)
  → api/conversations.ts        拼业务路径、选方法
  → api/client.ts               拼 /api/v1 前缀、加 token、fetch
  → fetch("/api/v1/conversations")
  → Vite 开发服务器 (:5173)      命中 proxy 规则
  → 转发到 http://127.0.0.1:8000/api/v1/conversations
  → FastAPI                      中间件 → 依赖 → 路由 → service → MySQL / DeepSeek
  ← 响应原路返回
  ← client.ts 拆掉信封，把 data 交给调用方
  ← 组件 setState → 界面更新
```

生产环境把 "Vite 开发服务器" 换成 "Nginx"，其余完全一样。

### 3.2 接口对照表

| 前端函数 | 方法 + 路径 | 请求体 | 需要 token |
| --- | --- | --- | --- |
| `authApi.register` | `POST /auth/register` | JSON | 否 |
| `authApi.login` | `POST /auth/login` | **表单** | 否 |
| `authApi.me` | `GET /auth/me` | — | 是 |
| `convApi.listConversations` | `GET /conversations?limit&offset` | — | 是 |
| `convApi.createConversation` | `POST /conversations` | 无 | 是 |
| `convApi.renameConversation` | `PATCH /conversations/{id}` | JSON | 是 |
| `convApi.deleteConversation` | `DELETE /conversations/{id}` | — | 是 |
| `convApi.listMessages` | `GET /conversations/{id}/messages` | — | 是 |
| `convApi.sendMessage` | `POST /conversations/{id}/chat` | JSON | 是 |

**三个容易踩的点：**

1. **登录收的是表单，不是 JSON**。这是 OAuth2 密码流规范硬性要求的。所以 `client.ts` 里专门有个 `form` 选项，用 `URLSearchParams` 拼 `application/x-www-form-urlencoded`。**注册反而是 JSON**（不受 OAuth2 约束）—— 同一个登录页上两个接口的请求格式不一样，这是最容易写错的地方。
2. **`POST /conversations` 不收请求体**。标题由后端给默认值"新对话"，改名走 `PATCH`。
3. **`POST /conversations` 可能返回"已存在的"会话**。后端不允许堆一堆空会话：如果该账号已经有一个没问过话的会话，直接返回它（见 PRD §5 的补充说明）。所以前端拿到返回值后**不能盲目往列表前面插一条**，否则会出现重复项 —— 正确做法是重新拉一次列表。

### 3.3 登录态是怎么维持的（完整链路）

```text
① 登录成功
   AuthContext.login() → setToken(res.access_token) 写进 localStorage
                       → setUser(res.user)

② 之后每一次请求
   client.ts 里 getToken() 拿到它，自动加到
   Authorization: Bearer <token> 请求头

③ 后端校验
   FastAPI 的 oauth2_scheme 从请求头抠出 token
   → get_current_user 验签 + 查库 → 注入 current_user

④ token 失效（过期 / 被篡改 / 用户被删）
   后端返回 401 → client.ts 捕获 → clearToken() + location.replace('/login')

⑤ 刷新页面
   token 还在 localStorage，但状态是空的
   → AuthProvider 的 useEffect 拿 token 换一次 /auth/me
   → 成功：恢复登录态；失败：清掉 token 回到登录页
```

**前端不解析 JWT。** 它只把 token 当一个不透明的字符串存着、带上。**"这个 token 是谁的、有没有过期"由后端说了算** —— 这是刻意的，前端解析 token 是多余且不安全的行为。

### 3.4 一次完整的数据流：从"点登录"到"屏幕上出现回答"

**前半段：登录**

1. 用户在 LoginPage 的表单里填完，点提交 → AntD Form 的 `onFinish` 拿到 `{username, password}`
2. 调用 `useAuth().login(...)`（来自 AuthContext）
3. → `authApi.login` → `request('/auth/login', { form: {...} })`
4. `client.ts`：拼成 `/api/v1/auth/login`，POST 表单，`auth: false` → **不带 Authorization 头**
5. Vite 代理转发到后端
6. 后端 `routers/auth.py::login` → `user_service.authenticate`（按用户名查库 + 校验密码哈希）→ 签发 JWT → 返回**扁平**的 `{access_token, token_type, user}`
7. `client.ts` 发现响应里没有 `code`/`data` → 原样返回
8. AuthContext：写 token、设 user
9. `navigate('/chat')` → 路由匹配到 ChatPage → `RequireAuth` 确认 user 有值 → 渲染

**后半段：提问**

10. ChatPage 的两个 `useEffect` 分别拉会话列表和消息历史 → MessageList 渲染出来
11. 用户在输入框敲字，回车或点发送 → `MessageInput` 调 `onSend(text)`
12. `handleSend`：**先乐观插入**一条用户气泡，然后 `setStreamingText('')`
13. → `convApi.sendMessage(convId, text, onDelta)`
14. 后端 `chat_service.reply` 依次做六件事：
    1. 存用户消息（**先落库再调模型**）
    2. 取该会话最近 10 条**已完成**的消息作为上下文
    3. 拼成 `[system prompt, ...历史]` 发给 DeepSeek
    4. 存 assistant 消息（带 `model_name`）
    5. 刷新会话的 `last_message_at`（列表排序依据）
    6. 返回 assistant 消息
15. 前端拿到回答 → `onDelta` 被调用一次（非流式，所以是一次性的）→ `setStreamingText(null)` → 把回答追加进 `messages`
16. `refreshConversations()` 再拉一次左侧列表 —— 因为 `last_message_at` 变了，**排序可能变**，不刷新的话列表顺序会和后端不一致

### 3.5 阶段 F 的流式预留（重要）

`sendMessage` 的签名**已经按流式设计**：

```ts
sendMessage(conversationId, content, onDelta: (text: string) => void): Promise<MessageOut>
```

现在的实现是"请求完，把整段文本一次性交给 `onDelta`"。阶段 F 改成流式时，**只改这个函数的内部**：

```ts
// 阶段 F 的样子（示意）
const res = await fetch(url, { method: 'POST', headers, body })
const reader = res.body.getReader()          // 逐块读
const decoder = new TextDecoder()
// 解析 event: message / data: {"delta": "..."} 这样的行
// 每收到一个 delta 就 onDelta(delta)
```

**UI 层一行都不用动** —— `MessageList` 已经在显示 `streamingText` 了，只要它逐字变长，界面上就是逐字输出。

⚠️ 阶段 F 的另一个知识点：**不能用 `EventSource`**。它虽然也叫"SSE 客户端"，但**不能自定义请求头**，而我们的接口全都需要 `Authorization: Bearer`。所以只能用 `fetch` + `getReader()` 手动解析。这一点写在 PRD §8.2 第 10 项。

---

## 4. 关键决策清单

| # | 决策 | 理由 | 没选什么 |
| --- | --- | --- | --- |
| 1 | **Vite 代理，后端不配 CORS** | 与生产 Nginx 的同源架构一致；前端始终写相对路径 | 后端加 `CORSMiddleware`（要处理预检、header 白名单，且和生产架构不符） |
| 2 | **token 存 localStorage** | 简单直接；阶段一没有 XSS 高风险的第三方内容 | httpOnly cookie（需要后端配合 + CSRF 防护，阶段一不做） |
| 3 | **用 React Context，不用 Redux** | PRD 明确不引入 Redux；登录态用 Context 足够 | Redux / Zustand / MobX |
| 4 | **401 在 `client.ts` 一处收口** | 业务代码不用重复写"失败了要跳登录" | 每个页面自己判断 |
| 5 | **`sendMessage` 按流式签名写、非流式实现** | 阶段 F 零返工 | 先按非流式写、阶段 F 再改调用方 |
| 6 | **登录走表单、注册走 JSON** | 后端就是这么定义的（OAuth2 规范要求密码流用表单），前端如实跟随 | 强行统一成 JSON（会破坏 Swagger 的 Authorize 按钮） |
| 7 | **Markdown 渲染 + DOMPurify 消毒** | 模型输出本来就带 Markdown，不渲染会看到一堆裸星号；消毒是安全底线 | 只渲染不消毒（XSS 漏洞） |
| 8 | **不用 AntD 的 `List` 组件** | AntD 6 已把它标记为废弃（建议换 `Listy`），会话列表自己十几个 div 就够 | 继续用 `List`（控制台会一直警告，且未来大版本会移除） |
| 9 | **`fetch` 而不是 axios** | 原生 API，不引入额外依赖；需求简单 | axios |
| 10 | **只对聊天气泡和少量布局用内联样式** | AntD 没有现成的聊天组件；其余全部用 AntD 默认样式，符合 PRD §6"不手写样式" | 全手写 CSS / 引入样式方案 |

---

## 5. 已知边界与未做的事

**性能/体验类（阶段 F、P1 处理）：**

- **非流式**：目前要等模型全部说完才显示（阶段 F 改成逐字）
- **没有"停止生成"**（F17，P1）
- **消息一次拉 100 条，没有无限滚动**（F19，P1）
- ⚠️ **消息列表首屏拉的是"最早的 100 条"而不是"最近的 100 条"** —— 后端接口目前是 `limit/offset` 正序。超长会话会看不到最新消息。这是阶段 E 就记下来的已知问题，等做 F19（滚到顶加载更早）时一起改成游标分页
- ⚠️ **时间显示差 8 小时**：后端返回的是不带时区标记的 UTC 字符串（如 `2026-09-25T10:38:38`），浏览器会当成本地时间解析。目前界面没显示时间所以看不出来；一旦要显示，需要前端补一个 `Z`，或者后端序列化时带上 `+00:00`

**故意的取舍（PRD 明确不做）：**

- 没有移动端适配（PRD §6）
- 没有多语言（i18n）
- 没有第三方登录、找回密码

**测试相关：**

- 端到端测试是 Playwright 脚本（存在开发机的工作目录，不在仓库里），不是正式测试框架。正式冒烟测试是 PRD 的 F20（pytest，P1）

---

## 6. 可能会被问到的问题

**Q：前端怎么知道用户已经登录了？**
A：两处配合。① `localStorage` 里存了 token；② 页面加载时用它调一次 `/auth/me`，后端确认有效才算已登录。前端**不解析 token 内容** —— 那是后端的职责。

**Q：token 过期了会怎样？**
A：后端返回 401 → `client.ts` 捕获 → 清掉 token 并跳转登录页。业务代码不需要处理这件事。

**Q：前后端是两个端口，为什么不用配跨域？**
A：因为前端只请求自己所在的域名。开发环境由 Vite 的 proxy 转发到后端，生产环境由 Nginx 转发。浏览器看到的是同源请求，所以不需要 CORS。这样开发和生产的行为也完全一致。

**Q：为什么登录用表单、注册用 JSON？**
A：后端定的。登录受 OAuth2 密码流规范约束，必须用表单字段 `username`/`password`；注册不受这个规范限制，用 JSON 更自然。前端如实跟随后端的定义。

**Q：为什么要用 `DOMPurify`？**
A：模型的回答里带 Markdown，需要转成 HTML 才能显示（加粗、列表）。这些 HTML 来自不可信来源（模型，阶段二还有知识库文档），直接塞进页面就是 XSS 漏洞。`DOMPurify.sanitize` 会把危险标签和属性洗掉。

**Q：为什么不用 axios？**
A：需求简单，原生 `fetch` 够用，还能少一个依赖。`client.ts` 那七十来行已经把 axios 常用的能力（统一前缀、拦截器式的 401 处理、自动带 token）都覆盖了。

**Q：这个项目里 AI 参与了多少？**
A：**如实答即可。** 事实是：需求、PRD、技术选型决策、各阶段的验收和 Review 是你做的（仓库里有 4 次 PRD 变更记录、以及每次验收的验证过程）；前端的代码实现由 AI 完成，你负责验收和提修改意见（比如"不允许堆空会话"这条规则就是你提出来的）。后端则是你按 PRD 分阶段实现的，AI 负责讲解和 Review。**commit 历史里也标注了哪次提交是 AI 接管的。**

**Q：如果后端接口改了，前端要改哪里？**
A：改 `src/api/` 下对应的函数 + `src/types/api.ts` 里的类型。界面组件基本不用动 —— 这正是把网络请求单独分层的目的。

**Q：为什么消息用 `id` 排序而不是 `created_at`？**
A：`DATETIME` 只有秒级精度，同一秒内插入的多条消息（用户消息 + 回答）时间戳会相同，排序就不确定了。`id` 自增，永远不会撞。

---

## 7. 想深入前端时的学习顺序

如果要补前端知识，按这个顺序最省力（每个都对着仓库里的真实代码看）：

1. **React 三件套**：`useState` / `useEffect` / 列表渲染 → 看 `ChatPage.tsx` 和 `MessageList.tsx`
2. **props 和组件拆分** → 看 `components/` 下的五个文件，注意它们怎么通过 props 和父组件通信
3. **Context（跨层级共享状态）** → 看 `AuthContext.tsx`
4. **TypeScript 的基础用法** → 看 `types/api.ts`（interface）和组件里的 props 类型
5. **React Router** → 看 `App.tsx` 和 `RequireAuth.tsx`
6. **异步与状态** → 看 `client.ts` 和 `ChatPage.tsx` 里的 loading / error 处理
7. （阶段 F 之后）**流式读取响应** → 看那时的 `sendMessage`

参考项目 PRD §8.2 已经列好了：`fastapi-react-todo` 前端的 `TodoContext.tsx` 和 `frontend-tutorial.md`。
