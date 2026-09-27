# Morrow

> **An extensible LLM-RAG-Agent platform for medical knowledge and personalized health assistance.**
>
> 帮助今天的你，为明天的自己做得更好。

---

## 三阶段路线图

| 阶段              | 定位                                           | 核心产物                             | PRD                             |
| ----------------- | ---------------------------------------------- | ------------------------------------ | ------------------------------- |
| **阶段一ing!!!** | 全栈 AI 问答壳（注册登录、多会话、多轮、流式） | 可演示、可部署、可写进简历的全栈应用 | [docs/v1_prd.md](docs/v1_prd.md) |
| 阶段二            | RAG 超声知识库（毕设主体）                     | 有据可依、可溯源的问答 + 评估报告    | [docs/v2_prd.md](docs/v2_prd.md) |
| 阶段三            | Agent 化健康助手（加分项 / side project）      | 长期记忆 + tools + 主动交互          | [docs/v3_prd.md](docs/v3_prd.md) |

三者的关系：

- 阶段一是**底座**：不做完阶段一，阶段二无处挂载。
- 阶段二是**毕设主体**：决定毕设能不能过、能不能拿好成绩。
- 阶段三是**求职加分**：不是毕设必需项，优先级低于阶段一二与八股刷题。

演进方向：从「专业医疗知识问答」逐渐变成「个人健康知识与行动助手」。产品名取偏产品视角的 `Morrow`，不带 RAG、超声这类会变的专业词。

---

## 技术栈

> 当前锁定值，随进展持续更新。任何变更都应在对应 PRD 里留决策记录。

| 层         | 选型                                                    | 备注                                                                      |
| ---------- | ------------------------------------------------------- | ------------------------------------------------------------------------- |
| 前端       | HTML/CSS/JS + React 19 + TypeScript + Vite + Ant Design | 只学 React 一个框架；不引入 Vue / Next.js / Redux。**版本变更记录（2026-09-25）**：脚手架给的是 React 19 + AntD 6，是当前稳定组合且无 peer 依赖冲突，故不再强行降到 18 —— 对这个应用两者无实质差别。另引入 `react-router-dom`（PRD §6 已列）与 `marked` + `dompurify`（F21）                         |
| 后端       | Python 3.12 + FastAPI + SQLAlchemy 2.0 (async)          | ASGI 下统一用异步驱动，不用同步 Session                                   |
| 数据库     | MySQL 8                                                 | 存业务数据与知识库文本 / 元数据。**决策（2026-09-26）**：阶段二**不迁移** PostgreSQL —— 迁移成本高于收益，向量改走进程内 FAISS（理由见 [v2 PRD §3.1](docs/v2_prd.md)） |
| 向量检索   | FAISS（`faiss-cpu`，进程内）                              | **决策（2026-09-26）**：`IndexFlatIP` + L2 归一化（归一化后内积 = 余弦相似度）。规模为数千 chunk，精确检索足够，**不引入独立向量库 service**。抽象 `VectorStore` 接口留切换后路（pgvector / Qdrant 可后补） |
| 缓存       | Redis                                                   | 阶段一列为**可选**；消息全量落库，Redis 只做缓存/上下文，阶段二启用 |
| 大模型     | OpenAI 官方 SDK（openai 包，异步流式）                     | 用 DeepSeek 官方 API；生产统一用项目自己的 key，不做 BYOK。**变更记录（2026-09-25）**：原定 httpx 手写流式，改用官方 openai SDK —— 上游流式解析交给 SDK，阶段 F 自己那侧的 SSE 发送不受影响                                       |
| Embedding  | 硅基流动 `Qwen/Qwen3-Embedding-8B`（远程 API）             | **决策（2026-09-26）**：走 OpenAI 兼容的 `/v1/embeddings`，**不在本机运行模型**（不引入 torch、不下载权重，Docker 镜像保持轻量）。默认输出 4096 维；硅基流动是否支持 `dimensions` 降维待实测（见 [v2 PRD §3.1](docs/v2_prd.md)） |
| 部署运维   | Git + Linux + Docker + Docker Compose + Nginx           | 阶段一目标是`docker compose up` 一键起全栈                              |
| 文档解析   | MinerU（PDF → Markdown）                               | 阶段二知识库构建用                                                        |
| Agent 框架 | **未定**                                          | 阶段三再定，候选 LangChain / LangGraph / 自研 loop                        |

**明确不引入**：K8s、CI/CD、监控告警、消息队列、多租户、微服务拆分。

---

## 目录约定

```text
Morrow/
├── README.md            # 跨阶段内容：路线图、技术栈、目录约定
├── docs/
│   ├── v1_prd.md        # 阶段一 PRD：完整规格
│   ├── v2_prd.md        # 阶段二 PRD：毕设背景、检索链路与评估
│   ├── v3_prd.md        # 阶段三 PRD：愿景与开放问题
│   └── frontend_architecture.md  # 前端架构说明（架构 / 数据流 / 前后端交互）
├── references/          # 资料实体与链接清单（论文、外部文档、抓取素材）
├── backend/             # FastAPI 应用
└── frontend/            # React 应用
```

约定：

- **跨阶段的内容**（路线图、技术栈、目录约定）写在本文件。
- **阶段内可执行的内容**（功能清单、数据模型、API、页面、学习任务）写进对应 PRD，不在本文件重复。
- **学习资料与参考**写在**对应阶段的 PRD** 里：引用知识库内的本地文件用相对路径，线上资料用链接。资料的实体文件放 `references/`。
- 每份 PRD 只描述自己阶段，不越界描述其他阶段的实现细节。
