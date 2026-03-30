# RelaxAgent

一个正在演进中的“简单版 LobeHub”项目，当前采用：

- 前端：`Next.js + React + Zustand`
- 后端：`FastAPI`
- 架构：前后端分离，后端按 `DDD` 思路组织

## 目录结构

```txt
.
├── src/
│   ├── app/                # Next.js 页面
│   ├── components/         # 前端 UI 组件
│   ├── store/              # 前端状态管理
│   └── lib/                # 前端类型和 API 客户端
└── backend/
    ├── app/
    │   ├── domain/         # 领域模型、网关接口、异常
    │   ├── application/    # 用例编排
    │   ├── infrastructure/ # Provider 适配器
    │   ├── presentation/   # FastAPI 路由和 DTO
    │   └── shared/         # 配置
    └── pyproject.toml
```

## 当前支持

- OpenAI-compatible 协议
- Anthropic native 协议
- 内置 Agent
  - 通用助手
  - 写作助手
  - 代码助手
- 新建会话时选择 Agent
- 会话按 Agent 进行角色化聊天
- 前端从后端加载会话列表
- 新建会话、删除会话已接后端接口
- 会话本地保存
- 服务端 SQLite 会话持久化
- 流式聊天
- 设置页测试连通
- 会话级 token 用量展示

## 启动方式

先复制环境变量：

```bash
cp .env.example .env.local
```

启动前端：

```bash
npm install
npm run dev
```

启动后端：

```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install -e backend
cd backend
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

启动后访问：

- 前端：[http://localhost:3000](http://localhost:3000)
- 后端健康检查：[http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- 后端文档：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 交接文档

如果下次继续开发，先看：

- [docs/HANDOFF.md](/Users/xuzishuo/ai-work/relaxagent/docs/HANDOFF.md)

## 前后端交互

前端通过 `lib/api.ts` 调用独立后端：

- 默认后端地址：`http://127.0.0.1:8000/api/v1`
- 聊天接口：`POST /chat`
- Agent 接口：`GET /agents`
- 连通测试接口：`POST /providers/test`
- 会话接口：`GET /sessions`、`GET /sessions/{id}`、`POST /sessions`、`DELETE /sessions/{id}`
- 默认数据库：`backend/relaxagent.db`

如果需要换后端地址，修改：

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## 当前 DDD 落点

- `domain`
  - 聊天实体、Provider 类型、仓储接口、领域校验服务
- `application`
  - 聊天应用服务，负责编排 provider registry 和 session repository
- `infrastructure`
  - OpenAI-compatible / Anthropic provider 适配器
  - 基于 SQLAlchemy 的 session repository
- `presentation`
  - FastAPI 路由、DTO、依赖注入、统一错误处理

后续如果接数据库，优先替换：

- `backend/app/infrastructure/persistence/session_repository.py`

如果继续扩展模型厂商，优先补：

- `backend/app/infrastructure/providers/`
