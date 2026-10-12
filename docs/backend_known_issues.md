# 后端已知问题清单（阶段一重读产出）

> **状态**：工作清单，不是规格。产出时间 2026-10-09，来源是 2026-10-03 起对阶段一后端的逐层重读。
> **用法**：每条给出「现象 / 影响 / 建议 / 待决策」。**决定之后**把结论回写进 [v1 PRD](v1_prd.md)（或对应文档），本文档随之归档或删除。
> **前提**：本次重读确认后端的分层（router → service → ORM）、越权校验收进依赖、统一响应信封与全局异常处理都是干净的，**不需要重构**。下面都是点状问题——不改也不影响阶段一跑通，但会在联调或阶段二时暴露。

优先级标记：**★ 联调前必须定** / ○ 可现在改、也可延后 / △ 阶段二入口

---

## 已解决（保留记录，供回写 PRD 时参考）

| 编号 | 问题 | 解决方式 | 涉及文件 | 日期 |
| --- | --- | --- | --- | --- |
| B3 | 生成失败时不落库 | `except` 分支改为三步：先 `logger.exception`（带 traceback）→ 再落一条 `status='failed'` 的 assistant 消息（`content=''`、`error_message` 截断到 480 字符，列为 `VARCHAR(500)`）→ 最后再抛 502。保留 502 而不是改成 200 + failed 消息；`error_message` 不下发前端，前端靠 `MessageOut.status` 判断 | `app/services/chat_service.py`、`app/services/message_service.py` | 2026-10-12 |
| B2 | llm_service 每请求新建 OpenAI 客户端 | 新增 `app/core/llm_client.py`：客户端做成进程级资源，按 `(base_url, api_key)` 缓存复用，配置变了自动重建；新增 `app/core/lifespan.py`，应用退出时 `close()` 释放 httpx 连接池（`main.py` 传入 `lifespan=`） | `app/core/llm_client.py`（新）、`app/core/lifespan.py`（新）、`app/services/llm_service.py`、`app/main.py` | 2026-10-12 |
| B5 | engine 的 `echo=True` 硬编码 | `Settings` 增加 `SQL_ECHO: bool = False`，`create_async_engine(echo=settings.SQL_ECHO)`；`.env.example` 补说明，本地 `.env` 设 `true` 以保持原有行为 | `app/core/config.py`、`app/database/session.py`、`.env.example`、`.env` | 2026-10-12 |
| B10 | 只读查询的事务跨过了慢网络调用（做 B2 时顺带发现） | `llm_service.complete` 读到配置后先把值取成普通 Python 变量，再 `await db.commit()` 结束这次只读事务——否则那条连接会在 10–30 秒的网络调用期间一直被占住，并发一上来先耗尽 `pool_size` | `app/services/llm_service.py` | 2026-10-12 |
| B1 | 同一张表里有两套时间基准 | 统一为 **UTC + 应用层生成**：`app/database/base.py` 新增 `utcnow()`（返回 naive UTC，作为全库唯一时间来源）；`TimestampMixin` 的 `server_default=func.now()` / `onupdate=func.now()` 换成 `default=utcnow` / `onupdate=utcnow`；`conversation_service` 改用 `utcnow()`；`app/schemas/common.py` 新增 `UtcDatetime`（Pydantic `PlainSerializer`），出口给 naive UTC 补 `+00:00`，三个 schema 的 `created_at` / `last_message_at` 改用它。列类型保持 `DateTime`（秒精度，排序由 `id` 兜底），因此**不需要 DDL 改动** | `app/database/base.py`、`app/services/conversation_service.py`、`app/schemas/common.py`、`app/schemas/user.py`、`app/schemas/conversation.py`、`app/schemas/message.py` | 2026-10-12 |

> **尚未实跑验证的两处**（前端联调时会自然覆盖到）：B1 的**库写入路径**（新写入的行是否真的按 UTC 落库）与 B3 的**失败路径**，目前只做了代码层与序列化层的检查，没有对着真实 MySQL 跑一遍。

> **待回写 PRD 的结论（B3 的连带影响）**：失败消息会出现在 `GET /conversations/{id}/messages` 的返回里（`status='failed'`、`content` 为空串）。因此前端消息列表必须处理三种情况——正常文本、失败态、空内容，**不能假设"有回答就渲染文本"**。另：前端收到 502 后应重新拉一次消息列表，否则失败气泡不会出现。

---

## ○ B4 同一会话没有并发保护

- **位置**：`app/services/chat_service.py`（无锁）、`app/routers/conversations.py` 的 chat 端点
- **现象**：v1 PRD §7.1 第 8 条要求"同一会话同时只允许一个生成任务，重复发起返回 409"，**未实现**。两个标签页同时发送会在同一会话里插出两条回答。
- **影响**：数据错乱；上下文顺序取决于两次请求的完成先后。
- **建议**：进程内维护 `dict[conversation_id, 状态]` + 409，与后端单 worker 的现状一致（多 worker 才需要 Redis，见 PRD §7.1 第 9 条）。
- **待决策**：现在做，还是等 SSE 恢复时和 detach 一起做（两者共用同一套生成状态管理）。

## △ B6 建表只有 create_all，没有迁移工具

- **位置**：`backend/init_db.py`
- **现象**：`Base.metadata.create_all` 只建**不存在**的表；模型改了字段、重跑脚本**不会有任何效果也不报错**。
- **影响**：阶段二要给 `message` 加引用来源字段时，必须手工 `ALTER` 或引入迁移工具。
- **建议**：阶段二开工前定一次——手写 SQL 迁移文件（轻）或引入 Alembic（重但规范）。
- **待决策**：放在阶段二开头作为第一个决策点。

## △ B7 message.status 里两个枚举值在非流式下空转

- **位置**：`app/models/message.py` 的 `MessageStatus`
- **现象**：`streaming` / `interrupted` 是为流式与中断生成设计的；SSE 延后后这两个值永远不会出现（`streaming` 只是列默认值，实际写入都显式传 `COMPLETED`）。
- **影响**：无害，但会让读代码的人误以为存在流式逻辑。
- **建议**：保留枚举（恢复 SSE 时直接用），并在 B3 落地后至少让 `failed` 真正被用上。
- **待决策**：是否在 PRD §4.3 加一句"非流式阶段 streaming / interrupted 暂不产生"。

## ○ B8 文档有、代码没有：`GET /models`

- **位置**：v1 PRD §5 的 API 草案
- **现象**：`GET /models` 列在 API 草案里，代码里没有这个路由（`routers/` 只有 auth 与 conversations）。
- **影响**：不影响跑通；前端设置页若要显示当前模型就缺一个接口。
- **建议**：已在 PRD §5 标注【当前未实现】；做前端设置页时一并决定要不要补。
- **待决策**：前端是否保留"设置"页。

## ○ B9 后端目前没有任何自动化验证手段

- **现象**：`check_*.py` 四个手写验证脚本已在 2026-10-09 删除；PRD 的 F20（pytest 冒烟，P1）未实现。
- **影响**：后端改动后没有回归手段，只能靠前端联调或手工 curl 验证。
- **建议**：做前端之前先用 pytest 补 3–4 个最小冒烟用例（登录成功/失败、越权被拒、发消息 mock 模型），成本不高但能兜住后续所有后端改动。
- **决定（2026-10-12）**：**先跳过**。引入 pytest 的学习成本与阶段一剩余价值不成比例；暂时改由"前端联调时手工走通 4 条链路"充当回归手段，正式冒烟留到 P1（PRD 的 F20）。
- **低成本替代（可选，不需要学 pytest）**：写一个 `asyncio.run` 的脚本把 4 条链路串一遍（像已删除的 `check_*.py` 那样），约 40 行。哪天想要一层网再说。

---

## 重读中确认"不用改"的点（避免以后重复怀疑）

| 位置 | 结论 |
| --- | --- |
| 分层：router → service → ORM | 干净，职责清楚，不重构 |
| 越权校验返回 404 而非 403 | 正确，避免暴露资源存在性（PRD §5.1） |
| 注册 / 登录不走统一信封 | 正确，Swagger 的 Authorize 按钮需要 `access_token` 平铺在最外层（PRD §5.2） |
| `message` 上不给 `created_at` 单独建索引 | 正确，现有查询全部由 `(conversation_id, id)` 覆盖（PRD §4.3 说明 4） |
| 用 `asyncmy` 而非 `aiomysql`；用 `pwdlib[argon2]` 而非 `passlib[bcrypt]` | 正确，均有 PRD 变更记录 |
| `conversation.user_id` 不单独建索引 | 正确，复合索引 `ix_conversation_user_last_msg` 最左列即 `user_id` |
| 不用 Alembic（当前） | 阶段一可接受，但见 B6 |
