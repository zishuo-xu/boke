# Handoff Notes

最后更新：2026-03-14

## 当前状态

项目已经是可运行的前后端分离结构：

- 前端：`Next.js + React + Zustand`
- 后端：`FastAPI + DDD-style layering`
- 数据库：`SQLite`

## 已完成功能

- 基础聊天界面
- Agent 化会话
  - 内置通用助手
  - 内置写作助手
  - 内置代码助手
  - 新建会话时选择 Agent
- 会话列表、新建、删除、重命名
- 设置页模型配置
- 支持 `OpenAI-compatible`
- 支持 `Anthropic native`
- 设置页“测试连通”
- 连通测试错误分类与耗时展示
- 流式聊天
- 会话级 token 用量展示
  - 输入 token
  - 输出 token
  - 总计 token
- 后端 SQLite 会话仓储
- 前端启动后从后端加载会话列表
- 新建/删除会话已接入后端接口

## 当前关键文件

前端：

- `src/app/page.tsx`
- `src/app/settings/page.tsx`
- `src/components/chat/chat-shell.tsx`
- `src/components/session/session-sidebar.tsx`
- `src/components/settings/settings-form.tsx`
- `src/store/use-chat-store.ts`
- `src/store/use-settings-store.ts`
- `src/lib/api.ts`
- `src/lib/chat.ts`
- `src/lib/settings.ts`

后端：

- `backend/app/main.py`
- `backend/app/application/chat/services.py`
- `backend/app/domain/chat/entities.py`
- `backend/app/domain/chat/gateways.py`
- `backend/app/domain/chat/repositories.py`
- `backend/app/infrastructure/providers/openai_gateway.py`
- `backend/app/infrastructure/providers/anthropic_gateway.py`
- `backend/app/infrastructure/providers/provider_registry.py`
- `backend/app/infrastructure/persistence/session_repository.py`
- `backend/app/presentation/api/v1/routes/chat.py`
- `backend/app/presentation/api/v1/routes/providers.py`
- `backend/app/presentation/api/v1/routes/sessions.py`

## 启动方式

前端：

```bash
cd /Users/xuzishuo/ai-work/relaxagent
npm run dev
```

后端：

```bash
cd /Users/xuzishuo/ai-work/relaxagent/backend
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

访问地址：

- 前端：`http://localhost:3000`
- 后端健康检查：`http://127.0.0.1:8000/health`
- 后端文档：`http://127.0.0.1:8000/docs`

## 当前接口

- `POST /api/v1/chat`
- `GET /api/v1/agents`
- `POST /api/v1/providers/test`
- `GET /api/v1/sessions`
- `GET /api/v1/sessions/{id}`
- `POST /api/v1/sessions`
- `DELETE /api/v1/sessions/{id}`
- `GET /health`

## 已知注意点

### 1. CORS

如果前端不是通过 `localhost:3000` 或 `127.0.0.1:3000` 打开，而是通过局域网地址访问，比如 `192.168.x.x:3000`，后端会报 `CORS error`。

当前白名单配置在：

- `backend/app/shared/config.py`

### 2. Token 用量统计

当前 token 用量来自模型流式返回的真实 usage 事件：

- OpenAI-compatible：通过流式 usage 事件读取
- Anthropic：通过 messages stream 里的 usage 字段读取

但目前 token 用量只落在前端会话状态里，**还没有持久化进 SQLite**。

### 3. 会话持久化已部分切到后端

后端已经有 SQLite 会话仓储，前端启动时会从后端加载会话列表，新建/删除也会同步到后端。

也就是说：

- 当前能用
- 但还没有彻底切成“前端完全以后端消息详情和 token 数据为准”
- 重命名仍然是前端本地行为
- token 用量仍然主要保存在前端状态
- 当前 Agent 主要承担“角色/提示词”职责，模型连通信息仍沿用前端设置页传入

## 最近修复

- 设置页全部中文化
- 增加模型连通测试
- 连通测试返回结构化错误和耗时
- 增加每个会话的 token 用量展示
- 修复 OpenAI-compatible 流中 usage-only 事件导致的 `IndexError`

## 推荐下一步

优先级建议：

1. 会话数据流进一步以后端为准
   - 前端切到按需读取 `GET /sessions/{id}`
   - 增加服务端重命名接口
   - 减少本地 `localStorage` 对消息主数据的依赖

2. token 用量落库
   - 在 SQLite session/message 结构里保存 usage
   - 刷新后仍能看到历史 token 用量

3. 聊天错误体验继续优化
   - 将 provider 错误映射成更明确的中文提示
   - 区分网络错误、模型错误、额度错误

4. Provider 预设体验
   - OpenAI
   - Anthropic
   - DeepSeek

5. 会话能力补全
   - 服务端重命名
   - 搜索会话
   - 会话列表分页/排序优化

6. Agent 能力补全
   - Agent 编辑页
   - Agent 自定义模型配置
   - Agent CRUD

## 下次开发前建议先做的事

1. 拉起前后端
2. 打开设置页确认 provider 测试正常
3. 用一个真实模型发一条消息
4. 确认聊天流、token 统计、数据库写入都正常
