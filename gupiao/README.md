# 股票/基金数据监控+AI解读面板

一款面向个人投资者的轻量化金融数据工具，实现自选管理和数据监控两大核心功能，支持股票/基金实时数据展示、历史走势图表、价格预警等功能。

## 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: SQLite
- **数据获取**: AKShare
- **认证**: JWT (python-jose, passlib)

### 前端
- **框架**: 原生 JavaScript
- **图表**: ECharts 5.x
- **样式**: 原生 CSS

## 功能特性

- ✅ 用户系统：注册、登录、认证
- ✅ 自选管理：添加、删除、分组、搜索股票/基金
- ✅ 数据监控：实时数据展示、历史走势图表
- ✅ 价格预警：上限/下限预警、站内通知
- ✅ 响应式设计：PC/移动端适配
- 🔜 AI解读：预留接口，待实现

## 安装部署

### 环境要求
- Python 3.8+
- pip

### 安装步骤

1. 克隆项目
```bash
cd /Users/xuzishuo/ai-work/gupiao
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.example .env
```

编辑 `.env` 文件，设置 `SECRET_KEY` 等配置。

4. 启动服务
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. 访问应用
- 前端页面: http://localhost:8000/
- API文档: http://localhost:8000/docs

## 项目结构

```
gupiao/
├── app/                      # 后端应用
│   ├── api/v1/              # API路由
│   ├── models/              # 数据模型
│   ├── schemas/             # Pydantic验证
│   ├── services/            # 业务逻辑
│   ├── core/                # 核心模块（数据库、认证）
│   ├── utils/               # 工具函数
│   └── main.py              # FastAPI入口
├── frontend/               # 前端
│   ├── index.html           # 登录页
│   ├── app.html             # 主应用页
│   └── static/             # 静态资源
│       ├── css/            # 样式文件
│       └── js/             # JavaScript文件
├── data/                   # 数据目录
│   └── finance.db          # SQLite数据库
├── requirements.txt        # Python依赖
├── .env.example            # 环境变量示例
└── README.md              # 项目说明
```

## 使用说明

### 1. 用户注册/登录
首次使用需注册账号，提供邮箱和密码即可。

### 2. 添加自选标的
- 支持 A股、港股、美股、基金
- 可选择分组进行管理
- 支持代码或名称搜索

### 3. 查看实时数据
- 选择标的查看实时价格、涨跌幅等数据
- 支持多时间周期历史走势图表

### 4. 设置价格预警
- 为标的设置上限/下限预警
- 预警触发时接收站内通知

## API 文档

启动服务后访问 http://localhost:8000/docs 查看 Swagger API 文档。

## 免责声明

本工具仅提供金融数据参考，不构成任何投资建议。投资者据此操作，风险自担。市场有风险，投资需谨慎。

数据来源：公开金融数据平台（如东方财富、新浪财经等），仅供参考。

## 开发计划

- [ ] AI解读功能：对接 Claude API 实现智能分析
- [ ] 财经新闻：抓取并关联自选标的
- [ ] 收益计算器：持仓收益计算
- [ ] 数据导出：Excel/CSV 导出
- [ ] 邮件通知：预警邮件推送
- [ ] 定时刷新任务：后台自动刷新数据

## License

MIT License
