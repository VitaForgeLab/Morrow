# v1 PRD — 阶段一：全栈 AI 问答壳

> 上游：毕设背景见 [v2 PRD §0](v2_prd.md)；全局技术栈与目录约定见仓库 [README](../README.md)。
> 下游：[阶段二](v2_prd.md) 在本阶段的问答骨架上挂 RAG。
> 状态：**待开工**（本文件是阶段一的完整规格）

---

## 1. 阶段目标

一句话：**做一个可注册登录、可创建多个会话、支持多轮上下文与流式输出的 AI 问答全栈应用，并部署到线上。**

它的价值不在功能新奇（本质是 AI chat 套壳），而在于三件事：

1. 它逼你把**一条完整的全栈链路**跑通：浏览器 → React → HTTP/SSE → FastAPI → 鉴权 → MySQL → 大模型 API → 回流渲染。
2. 它是毕设的**最小可用骨架**：阶段二只需把"直接问模型"换成"先检索知识库再问模型"，其余全部复用。
3. 它是简历与面试的**可演示载体**：能当场打开、能演示、能讲清设计取舍。

**本阶段的技术关键词**：FastAPI 分层、异步 SQLAlchemy、MySQL、JWT、SSE 流式、多会话并行、生成任务 detach、React + TS 前端、Docker Compose。

---

## 2. 完成定义（DoD）

以"能当场演示下面这 9 条脚本"作为完成标准，**不是"代码写完了"**：

| # | 演示动作 | 验证了什么 |
| --- | --- | --- |
| 1 | 注册新账号 → 自动进入聊天页 | 注册 + 签发 token + 自动登录 |
| 2 | 新建会话 A，问"甲状腺超声检查前需要空腹吗"，看到逐字流式输出 | SSE 流式 |
| 3 | 在 A 里追问"那喝水呢"，回答体现对上一轮的引用 | 多轮上下文 |
| 4 | A 生成中，新建会话 B 并提问 | 多会话并行 |
| 5 | 切回 A，看到的是**完整回答**而不是半截 | 切走不丢（生成 detach） |
| 6 | 把 A 重命名为"甲状腺检查"，删除 B | 会话重命名 / 删除 |
| 7 | 刷新页面，历史仍在 | 落库 |
| 8 | 退出后用另一账号登录，看不到上面两个会话 | 越权校验 + 个人信息保护 |
| 9 | `docker compose up` 一条命令起全栈 | 部署 |

9 条全部走通 = 阶段一完成。

---

## 3. 功能清单

### P0（必做，缺一条即未完成）

**后端**

| 编号 | 功能 | 验收标准 |
| --- | --- | --- |
| F1 | 用户注册 | 用户名+密码；密码 bcrypt 哈希；用户名唯一，重复返回明确提示 |
| F2 | 用户登录 | 签发 JWT，返回 token + 用户信息；密码错误返回 401 |
| F3 | 鉴权依赖 | 受保护接口统一校验 token 并注入当前用户；无效 token 返回 401 |
| F4 | 会话 CRUD | 创建 / 列表（分页，按最近活跃排序）/ 重命名 / 删除（级联删消息） |
| F5 | 消息历史 | 按会话分页读取，支持正序加载 |
| F6 | 聊天接口 | SSE 流式生成；消息落库；带最近 N 条历史构建上下文 |
| F7 | 生成任务 detach | 客户端断开后生成继续，跑完后完整落库 |
| F8 | 模型配置表 | `model_config` 存 provider / base_url / model / 参数，代码从表读而非硬编码 |
| F9 | 统一响应与异常 | 统一 `{code, message, data}`；全局异常处理器；请求日志中间件 |
| F10 | 系统提示词与免责 | system prompt 含角色约束与拒答规则；阶段一最小实现（见 §7.5） |

**前端**

| 编号 | 功能 | 验收标准 |
| --- | --- | --- |
| F11 | 登录 / 注册页 | 标签页切换；错误提示；成功后写入本地并跳转 |
| F12 | 聊天主页 | 左侧会话列表 + 右侧聊天窗；新建/重命名/删除入口 |
| F13 | 流式渲染 | 逐字追加、自动滚到底、生成中状态、失败重试 |
| F14 | 会话操作 | 与 F4 对应，操作后列表即时更新 |
| F15 | 路由守卫 | 无 token 一律跳登录页 |
| F16 | 免责声明常驻 | 页面底部固定展示"不替代医生诊断" |

### P1（重要，可延后收尾）

| 编号 | 功能 | 说明 |
| --- | --- | --- |
| F17 | 中断生成（stop） | 生成中可停止，消息状态记 `interrupted` 或保留已生成部分 |
| F18 | 会话标题自动生成 | 用首条问题或一次轻量模型调用生成标题 |
| F19 | 历史消息无限滚动 | 滚到顶部加载更早消息 |
| F20 | pytest 冒烟测试 | 登录成功/失败、越权被拒、发消息（mock 模型） |
| F21 | Markdown 渲染 + XSS 防护 | `marked` + `DOMPurify.sanitize` |
| F22 | RAG 资料准备（非代码） | 收集甲状腺/颈动脉/腹部超声资料，MinerU 转 md；预习切片/embedding/检索概念 |

### P2（可选收尾，不阻塞验收）

| 编号 | 功能 | 说明 |
| --- | --- | --- |
| F23 | BYOK 多模型配置 | 用户在设置页填自己的 API key 与模型（`model_config` 表已预留字段） |
| F24 | Redis 缓存 | 会话列表热点数据 / 最近上下文缓存 |

### 明确不做（Out of scope）

- **RAG / 向量检索 / 引用来源展示** → 阶段二
- **Agent / 长期记忆 / 定时提醒 / 主动交互** → 阶段三
- 多模态（图片上传给模型、超声图像识别）
- 移动端 App / 小程序 / 移动优先的响应式适配
- 多语言 i18n
- 第三方登录（微信 / GitHub OAuth）、短信验证、找回密码
- 支付、团队协作、公开分享链接
- 生产级运维：K8s、CI/CD、监控告警、灰度发布

---

## 4. 数据模型

MySQL 8 / InnoDB / utf8mb4。四张表。

### 4.1 `user`

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | BIGINT | PK, auto_increment | |
| username | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | 登录名 |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt 哈希，绝不存明文 |
| nickname | VARCHAR(50) | NOT NULL | 展示名，默认同 username |
| created_at | DATETIME | NOT NULL | |
| updated_at | DATETIME | NOT NULL | |

> **个人信息最小化**（毕设课题要求 5）：阶段一只收用户名 + 密码，不收手机号、邮箱、真实姓名。

### 4.2 `conversation`

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | BIGINT | PK, auto_increment | |
| user_id | BIGINT | FK → user.id, NOT NULL, INDEX | |
| title | VARCHAR(100) | NOT NULL | 默认"新对话"，可重命名 |
| last_message_at | DATETIME | NOT NULL, INDEX | 会话列表排序依据 |
| origin | VARCHAR(20) | NOT NULL, 默认 'user' | 预留：阶段三"系统主动发起"（见 v3 §4） |
| created_at | DATETIME | NOT NULL | |
| updated_at | DATETIME | NOT NULL | |

索引：`(user_id, last_message_at DESC)` —— 会话列表的主查询走这条。
删除策略：硬删除，`message` 通过外键级联删除。

### 4.3 `message`

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | BIGINT | PK, auto_increment | |
| conversation_id | BIGINT | FK → conversation.id, NOT NULL, INDEX, ON DELETE CASCADE | |
| role | ENUM('system','user','assistant') | NOT NULL | |
| content | MEDIUMTEXT | NOT NULL, 默认 '' | |
| status | ENUM('streaming','completed','failed','interrupted') | NOT NULL | 见下方说明 |
| model_name | VARCHAR(50) | NULL | 记录本次生成用的模型，便于排查与统计 |
| error_message | VARCHAR(500) | NULL | `failed` 时记录原因 |
| created_at | DATETIME | NOT NULL, INDEX | |

> **`status` 是"切走不丢"的关键字段**。发起生成时先插入一条 `status='streaming'`、`content=''` 的 assistant 消息；生成过程中持续 UPDATE `content`；结束时改 `completed`。前端切回来看 `status` 就知道该渲染历史还是续流。
>
> 索引：`(conversation_id, id)` —— 按会话取消息、按时间排序。

### 4.4 `model_config`

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | BIGINT | PK, auto_increment | |
| name | VARCHAR(50) | UNIQUE, NOT NULL | 如 "deepseek-chat" |
| provider | VARCHAR(30) | NOT NULL, 默认 'openai-compatible' | |
| base_url | VARCHAR(255) | NOT NULL | |
| api_key | VARCHAR(255) | NOT NULL | **只存服务端配置，任何接口都不得下发前端** |
| model_name | VARCHAR(50) | NOT NULL | 传给 API 的 model 字段 |
| params | JSON | NULL | temperature / max_tokens 等 |
| is_default | TINYINT(1) | NOT NULL, 默认 0 | 唯一默认（应用层保证） |
| is_active | TINYINT(1) | NOT NULL, 默认 1 | |
| owner_user_id | BIGINT | NULL | NULL = 系统配置；非空 = 用户自带（P2 BYOK） |
| created_at | DATETIME | NOT NULL | |
| updated_at | DATETIME | NOT NULL | |

> 阶段一实际只需要**一行数据**（`is_default=1, owner_user_id=NULL`）。表先建好是为了：① P2 的 BYOK 不用改结构；② 面试里"模型可配置"这句话有代码支撑，而不是嘴上说。

### 4.5 表关系

```text
user ──1:N──> conversation ──1:N──> message
model_config ──(弱引用，不做外键)──> message.model_name
```

---

## 5. API 草案

统一前缀 `/api/v1`。除注册/登录外**全部需要** `Authorization: Bearer <token>`。

| 方法 | 路径 | 说明 | 鉴权 |
| --- | --- | --- | --- |
| POST | `/auth/register` | 注册，返回 token + user | 否 |
| POST | `/auth/login` | 登录，返回 token + user | 否 |
| GET | `/auth/me` | 当前用户信息 | 是 |
| GET | `/conversations` | 会话列表（分页） | 是 |
| POST | `/conversations` | 新建会话 | 是 |
| GET | `/conversations/{id}` | 会话详情 | 是 |
| PATCH | `/conversations/{id}` | 重命名 | 是 |
| DELETE | `/conversations/{id}` | 删除（级联消息） | 是 |
| GET | `/conversations/{id}/messages` | 历史消息（分页） | 是 |
| POST | `/conversations/{id}/chat` | 发起回答，返回 SSE 流 | 是 |
| GET | `/conversations/{id}/stream` | 只订阅当前生成流（切回 / 刷新后续流） | 是 |
| POST | `/conversations/{id}/stop` | 中断生成（P1） | 是 |
| GET | `/models` | 可用模型列表（阶段一返回默认那条） | 是 |

### 5.1 越权校验（必做）

所有带 `{id}` 的接口都必须校验 `conversation.user_id == current_user.id`。
不匹配时返回 **404 而不是 403** —— 避免暴露"该资源存在但不属于你"。

这条对应毕设课题要求 5 的"个人信息保护"，也是演示脚本第 8 条的考点。

### 5.2 非流式接口响应格式

统一响应：

```json
{ "code": 200, "message": "success", "data": {} }
```

统一错误：

```json
{ "code": 401, "message": "用户名或密码错误", "data": null }
```

### 5.3 SSE 事件约定（本项目自定义，以本 PRD 为准）

```text
event: message
data: {"delta": "甲状腺"}

event: message
data: {"delta": "超声检查前一般不需要严格空腹，但……"}

event: done
data: {"message_id": 123, "status": "completed"}

event: error
data: {"message": "上游模型调用失败"}
```

约定要点：

- 使用标准 SSE 的 `event:` + `data:` 双行格式，前端可按事件类型分发（比裸 `data: {json}` + `data: [DONE]` 更规范）。
- **参考项目 recyle 用的是裸 `data: {json}` + `[DONE]`，思路一致但约定不同 —— 抄它的流式代码时记得改这里。**
- 响应头 `Content-Type: text/event-stream`，并加 `X-Accel-Buffering: no`（否则经过 Nginx 会被缓冲，流式变一次性）。
- 错误也要通过 SSE 事件下发（连接建立后 HTTP 状态码已经发出，无法再改）。

---

## 6. 页面清单

| 路由 | 页面 | 内容 |
| --- | --- | --- |
| `/login` | 登录 / 注册 | 标签切换，用户名 + 密码 |
| `/chat` | 聊天主页 | 左侧会话列表（新建 / 重命名 / 删除 / 按活跃排序）+ 右侧聊天窗（消息流 + 输入框 + 生成中状态） |
| `/chat/:conversationId` | 同上，定位到指定会话 | |
| `/settings` | 设置 | 显示当前模型；P2 加 BYOK 配置 |

- 前端用 `react-router-dom`（两个参考项目都没用到，**需另学**）。
- 路由守卫：无 token 一律跳 `/login`。
- UI 全部用 Ant Design，**不手写样式、不做移动端适配**。
- 页面底部常驻免责声明：**"本系统仅供健康科普与检查流程咨询，不替代医生诊断与治疗建议。"**

---

## 7. 关键技术难点与设计决策

### 7.1 切走不丢：生成任务 detach（本阶段最难的一块）

**问题**：切换会话时前端会 abort 掉 SSE 请求。如果生成逻辑挂在请求生命周期上，回答就丢了——用户切回来只看到半截甚至空消息。

**方案**：

1. 发起生成时**先落一条** `status='streaming'`、`content=''` 的 assistant 消息（拿到 message_id）。
2. 用 `asyncio.create_task()` 启动生成协程。**这个 task 不随 HTTP 请求取消而取消** —— 这是整个方案的支点。
3. 生成协程内部**自己开一个数据库 session**（`async with AsyncSessionLocal() as s`），**不能复用请求注入的 `get_db()` session**，那个会随请求关闭。
4. 生成过程中周期性（约 0.5s，或每积累 N 个字符）UPDATE 该消息的 `content`。
5. 正常结束：`status='completed'`；异常：`status='failed'` 并写 `error_message`。
6. 前端切回：`GET /messages`。若最后一条 assistant 消息 `status='streaming'` → 连 `GET /conversations/{id}/stream` 续流；否则直接渲染历史。
7. `GET /stream` 的实现：进程内维护 `dict[conversation_id] -> 订阅者队列集合`，生成协程每产出一个 chunk 就广播给所有订阅者。
8. **同一会话同时只允许一个生成任务**，重复发起返回 409。
9. **已知边界（必须写清楚）**：进程内广播只在**单 worker**（`uvicorn --workers 1`）下成立。多 worker 需要 Redis Pub/Sub —— 而 Redis 在阶段一是 P2 可选项，所以**阶段一明确锁定单 worker**，并在 README 与本文档写明该限制。这是一个诚实的设计边界，也是面试可以讲深度的点。

**参考实现（待读，遇到问题再翻）**：开源 chat 应用里已有成熟做法，例如 [Operit](https://github.com/AAswordman/Operit)。先备注在此，不要在动手前通读别人的代码。

**降级预案**：若 detach 实现卡住，先做简化版 —— 前端不 abort，把流留在后台读完并写入全局 store（切会话只是隐藏组件）。先保住演示脚本第 4、5 条，之后再升级为后端 detach。

### 7.2 上下文构建

- 每次请求取该会话**最近 N 条 `status='completed'` 的消息**（N 先取 10，后续按 token 预算裁剪）。
- 组装顺序：`system prompt`（含角色约束与拒答规则） → 历史消息 → 本轮用户消息。
- 阶段一**不用 Redis、不做摘要压缩**。超长对话的裁剪策略（滑动窗口 / 摘要）列为阶段二议题。

### 7.3 鉴权

- 标准 `Authorization: Bearer <token>`，后端依赖里自己 strip 掉 `Bearer ` 前缀。
- 密码用 `passlib[bcrypt]` 哈希；JWT 用 `PyJWT` 或 `python-jose`，HS256，有效期 7 天。
- **不要抄参考项目 recyle 的裸 token + `user_token` 表方案** —— 它的 docstring 写着 JWT，实际代码是 UUID 存表，两者都不是标准做法。
- 阶段一不做 refresh token、不做多设备登出、不做权限角色体系。

### 7.4 ASGI 下的数据库

- 一律异步：`create_async_engine` + `async_sessionmaker` + `aiomysql` 驱动。
- **不要**在 `async def` 路由里使用同步 `Session` —— 参考项目 `fastapi-react-todo` 正是这个反面例子（`async def` 路由 + 同步 `sqlmodel.Session`），会阻塞事件循环。这一点要能讲清楚为什么。
- 连接池参数：`pool_pre_ping=True`、`pool_recycle=3600`、`pool_size=5`、`max_overflow=10`。

### 7.5 医疗安全钩子（毕设要求 5 的阶段一最小实现）

- `system prompt` 写死约束：只回答检查流程 / 准备事项 / 科普解释；遇到诊断、用药、急症症状 → 明确拒答并引导就医。
- 前端常驻免责声明（§6）。
- 会话与消息的越权校验（§5.1）。
- 个人信息最小化：只收用户名与密码（§4.1）。
- 后续（阶段二）升级为规则 + 分类双保险，并加日志脱敏。

---

## 8. 学习任务与参考

原则：**先跑通，再补原理。** 每项都写清"学到什么程度"（边界）和"参考哪里"。
引用约定：本地文件用相对路径（相对于本文件），线上资料用链接。资料的实体文件放 `references/`。

### 8.1 参考项目（只读，不做修改）

| 项目 | 位置 | 主要用来学 |
| --- | --- | --- |
| fastapi-react-todo | [本地](<../../../2 Fullstack Dev/20 Raw/v1_study_resourse/fastapi-react-todo>) | 前端工程结构（组件拆分 / Context 状态 / `api/` 层 fetch 封装 / TS 类型）+ FastAPI 基础分层（APIRouter / Schema 拆分 / Service 层 / CORS） |
| recyle | [本地](<../../../2 Fullstack Dev/20 Raw/v1_study_resourse/recyle>) | 异步 SQLAlchemy 与连接池、SSE 流式（服务端 + 前端消费）、统一响应与统一异常、请求日志中间件 |

> 两者都**不覆盖**的部分（多会话模型、`model_config`、生成任务 detach、部署）由本项目自行设计，设计见 §7。

### 8.2 要学（按依赖顺序）

| # | 内容 | 学到什么程度（边界） | 参考 |
| --- | --- | --- | --- |
| 1 | 前端三件套 | HTML 结构 / CSS 盒模型 + Flex / JS DOM + 事件 + fetch。**不求**手写复杂布局与动画 | [Frontend crashcourse.md](<../../../2 Fullstack Dev/20 Raw/Frontend crashcourse.md>) |
| 2 | React 最小集 | props / useState / useEffect / 列表 key / 受控表单 / Context / fetch 调 API 与 loading-error 态。**不学** Redux、Next.js、SSR、性能优化、fiber 原理 | [TodoContext.tsx](<../../../2 Fullstack Dev/20 Raw/v1_study_resourse/fastapi-react-todo/frontend/src/context/TodoContext.tsx>)、[frontend-tutorial.md](<../../../2 Fullstack Dev/20 Raw/v1_study_resourse/fastapi-react-todo/Document/frontend-tutorial.md>) |
| 3 | TypeScript 够用量 | 给 props 与 API 响应写 `interface`，可选字段用 `?`。**不学**泛型体操、装饰器、复杂类型推导 | [types/todo.ts](<../../../2 Fullstack Dev/20 Raw/v1_study_resourse/fastapi-react-todo/frontend/src/types/todo.ts>) |
| 4 | react-router-dom | 配 3 条路由 + 路由守卫。**不学**嵌套路由高级用法、loader/action | [官方文档](https://reactrouter.com/start/declarative/installation)（参考项目里没有） |
| 5 | APIRouter 拆分 | 按业务拆 router + `prefix`/`tags` + 在 main 组装 | [backend/app/routers/](<../../../2 Fullstack Dev/20 Raw/v1_study_resourse/fastapi-react-todo/backend/app/routers/>) |
| 6 | 异步 SQLAlchemy | 异步引擎 / 会话工厂 / `get_db` 依赖 / `select()` 语法。**要能讲清**"为什么 async 路由里不能用同步 Session" | [db_config.py](<../../../2 Fullstack Dev/20 Raw/v1_study_resourse/recyle/News/Admin/config/db_config.py>)、[官方 asyncio 文档](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) |
| 7 | SQLAlchemy 2.0 建模 | `Mapped` / `mapped_column` / FK / 索引 / 关系 / comment | [models/users.py](<../../../2 Fullstack Dev/20 Raw/v1_study_resourse/recyle/News/Admin/models/users.py>) |
| 8 | JWT 认证 | 密码哈希 + 签发/校验 token + 受保护路由依赖。**不学** refresh token、OAuth2 授权码流程 | 自己笔记 [2.FastAPI.md](<../../../2 Fullstack Dev/21 Backend Dev/2.FastAPI.md>) 认证一节、[官方 Security 教程](https://fastapi.tiangolo.com/tutorial/security/) |
| 9 | SSE 服务端 | `StreamingResponse` + 事件格式约定 + 客户端断开后的行为 | [routers/ai.py](<../../../2 Fullstack Dev/20 Raw/v1_study_resourse/recyle/News/Admin/routers/ai.py>)（注意事件格式差异）、[MDN SSE](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) |
| 10 | SSE 前端消费 | `fetch` + `response.body.getReader()` + `TextDecoder` + 按行缓冲解析。**要懂**为什么不用 `EventSource`（它不能自定义 Authorization 头） | [AIChat.vue](<../../../2 Fullstack Dev/20 Raw/v1_study_resourse/recyle/News/App/src/views/AIChat.vue>) 的 `sendMessage()` |
| 11 | 统一响应 / 异常 / 日志 | `register_exception_handlers` 模式 + 请求日志中间件 + 统一 `{code,message,data}`。**注意**参考项目的 handler 存在 bug（`HTTP_INTERNAL_SERVER` 拼错、`IntegrityError` 注册成 `InterruptedError`），只学模式不抄实现 | [recyle utils/](<../../../2 Fullstack Dev/20 Raw/v1_study_resourse/recyle/News/Admin/utils/>) |
| 12 | 多会话并行 + 生成 detach | `asyncio.create_task` + `status` 字段 + 进程内广播 + 前端续流。**无现成参考，自己设计** | 本 PRD §7.1、[Operit](https://github.com/AAswordman/Operit)（待读） |
| 13 | MySQL 基础 | 建库建表 / 索引 / 事务 / 会用 `EXPLAIN` 看一次。**不学**主从复制、分库分表 | 自己笔记 [3.MySQL.md](<../../../2 Fullstack Dev/21 Backend Dev/3.MySQL.md>) |
| 14 | Docker Compose 部署 | 写 3 个 service（mysql / backend / frontend）+ 前端多阶段构建 + 环境变量注入。**不学** K8s、Swarm、CI/CD | 自己笔记 [docker.md](<../../../2 Fullstack Dev/23 Toolbox/docker.md>)（需先补） |
| 15 | pytest 冒烟 | 2–4 个用例：登录成功/失败、越权被拒、发消息（mock 模型）。**不学**覆盖率体系、复杂集成测试 | [官方 Testing 教程](https://fastapi.tiangolo.com/tutorial/testing/) |
| 16 | Markdown + XSS 防护 | `marked` 渲染 + `DOMPurify.sanitize`；React 用 `dangerouslySetInnerHTML` 时**必须**保留 sanitize | [AIChat.vue](<../../../2 Fullstack Dev/20 Raw/v1_study_resourse/recyle/News/App/src/views/AIChat.vue>)、[DOMPurify](https://github.com/cure53/DOMPurify) |
| 17 | RAG 资料准备（非代码） | 收集甲状腺/颈动脉/腹部超声资料并用 MinerU 转 md；预习切片 / embedding / 检索概念 | [v2 PRD](v2_prd.md) |

### 8.3 明确不学（阶段一不碰）

- Redux / Next.js / SSR / Vue
- Redis / Celery / RabbitMQ（Redis 仅在 P2 可选启用）
- LangChain / LangGraph / 向量库 / embedding 与 rerank 模型细节
- PostgreSQL / pgvector
- K8s / CI-CD / 监控告警
- SQLAlchemy 高级特性（关系加载策略调优、事件监听、自定义类型）
- React 原理层（fiber、虚拟 DOM diff、并发特性）

---

## 9. 风险与依赖

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| 前端从零起步，是**最长关键路径** | 拖住整体进度 | UI 全用 AntD；参考项目照着改；集中把 React 最小集先啃下来 |
| 生成 detach 无现成参考 | 可能卡住 | 先跑前端保活简化版；参考开源 chat 应用（§7.1）；必要时降级为 P1 |
| Docker 从零学 | 收尾超期 | 只做"能起"，不做调优；先把 `docker.md` 笔记补上 |
| 功能范围膨胀 | 迟迟没有可演示版本 | 严格按 P0 → P1 → P2 顺序推进；先跑通非流式全链路，再上流式 |
| 本地 shell 环境不可用（`spawn D:\Git\bin\bash.exe ENOENT`） | 无法本地跑通验证，"跑通才算学完"这条原则失效 | 修复 Git Bash 路径或重启编辑器后再开工 |
| 同一会话并发生成 | 数据错乱 | 单会话单生成任务，重复请求返回 409 |
| 上游模型 API 不稳定 / 限流 | 演示失败 | 统一走 `model_config` 便于换供应商；失败落 `status='failed'` 并支持重试 |

---

## 10. 与毕设的关系

阶段一不是"额外的练手项目"，**它就是毕设的骨架**。毕业设计的课题名称、7 条课题要求与 5 条研究重点见 [v2 PRD §0](v2_prd.md)。

| 毕设要求 | 阶段一的覆盖情况 |
| --- | --- |
| 要求 1：调研 LLM / 智能问答 / 语义检索 / RAG | 阶段一的选型过程即调研素材，注意留决策记录（本 PRD §7 与 README 技术栈表） |
| 要求 3：文档处理、语义检索、答案生成、多轮对话 | 答案生成 ✅、多轮对话 ✅；文档处理与语义检索 → 阶段二 |
| 要求 4：Web 界面、提问、历史记录、答案来源展示 | 前三项 ✅；来源展示 → 阶段二 |
| 要求 5：风险提示、敏感问题、个人信息保护 | 阶段一埋最小钩子（§7.5），阶段二加固 |
| 研究重点 4：多轮对话管理 | 阶段一实现基础版（最近 N 条上下文）；阶段二升级为带检索上下文的多轮 |

**因此阶段一必须能"讲"**：不只是跑得起来，还要能说清每个设计决策的理由。答辩与面试问的是"为什么这么设计"，不是"用了什么框架"。
