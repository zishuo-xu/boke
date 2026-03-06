# AI机器人狼人杀（Python后端 + Web前端）

## 项目说明
- 前端：`index.html + styles.css + app.js`，负责可视化展示与交互控制。
- 后端：`backend/app.py`，使用 Python Flask 提供游戏引擎与 API。
- 存储：游戏对局数据为后端内存态（无持久化）；LLM 配置会持久化到 `backend/llm_config.json`。

## 已实现能力
- 6-12 人局角色分配与自动流程（夜晚、天亮、发言、投票、胜负判定）。
- AI 角色逻辑：狼人、预言家、女巫、猎人、村民、守卫。
- 思考过程结构化展示、按玩家回溯、打字机回放/暂停/复制。
- 游戏控制：开始、暂停、继续、重置、速度切换。
- LLM 动态配置：`mock` / `openai` / `glm`（失败自动回退 mock）。
- 三栏可视化布局：玩家区、主场景流程、思考面板。
- 完整对局记录与胜负统计展示。

## 运行方式
1. 安装依赖：

```bash
cd /Users/xuzishuo/ai-work/wolf
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. 启动服务：

```bash
python3 backend/app.py
```

3. 浏览器访问：
- [http://127.0.0.1:8000](http://127.0.0.1:8000)

## API 概览
- `GET /api/state`：获取当前对局状态
- `POST /api/config/game`：设置人数/速度/身份展示策略
- `POST /api/config/llm`：设置模型提供方与参数
- `POST /api/game/start`：开局/继续
- `POST /api/game/pause`：暂停
- `POST /api/game/resume`：继续
- `POST /api/game/reset`：重置

## 说明
- 当前为单房间内存态；关闭后端进程后对局数据会丢失。
- 若需要多房间、多用户隔离、持久化或鉴权，可在此基础上继续扩展。
