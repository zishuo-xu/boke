# 极简自然语言饮食热量追踪器（V1 初版）

## 已实现（首版）
- Python FastAPI 后端 + SQLite 单文件数据库（自动初始化建表）
- 个人信息与营养目标管理（自动计算 + 手动覆盖）
- 自然语言饮食解析（LLM 可选 + 本地兜底解析）
- 饮食记录增删改查、按日期查询
- 每日营养看板（热量 + 三大营养素 + 餐次统计）
- 每日 AI 建议（LLM 可选 + 规则兜底）
- LLM 配置和提示词模板持久化
- CSV 导出、数据库备份下载
- 前端单页（移动端可用）

## 目录
- `backend/app`: 后端源码
- `frontend/index.html`: 前端页面
- `data/fitness.sqlite3`: 运行后自动创建

## 启动
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

前端直接打开：
- `frontend/index.html`

或用任意静态服务启动 `frontend/` 目录。

## 关键接口
- `GET /profile` / `PUT /profile`
- `GET /llm-config` / `PUT /llm-config`
- `POST /entries/parse`
- `POST /entries` / `GET /entries?entry_date=YYYY-MM-DD`
- `PUT /entries/{id}` / `DELETE /entries/{id}`
- `GET /summary/day?target_date=YYYY-MM-DD`
- `GET /summary/week?end_date=YYYY-MM-DD`
- `GET /export/csv`
- `GET /backup/db`
