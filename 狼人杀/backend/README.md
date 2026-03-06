# AI机器人狼人杀Web项目

一个基于Python Flask开发的AI机器人狼人杀游戏，支持多个AI机器人自主博弈，实时可视化AI的思考过程和操作。

## 项目特点

- 🤖 **AI自主博弈**：多个AI机器人根据角色逻辑自主决策
- 🎮 **完整游戏流程**：遵循狼人杀标准规则，自动推进游戏
- 💭 **思考过程可视化**：实时展示每个AI的思考过程
- 🎨 **优美界面**：现代化的Web界面设计，流畅的交互体验
- ⚡ **游戏控制**：支持调节游戏速度、暂停/继续、重置游戏
- 🔌 **LLM集成**：支持OpenAI和Anthropic API（可选使用模拟AI）

## 功能特性

### 游戏配置
- 支持6-12人局游戏
- 自动角色分配
- 游戏速度控制（快/中/慢）

### 角色支持
- 🐺 狼人
- 👨‍🌾 村民
- 🔮 预言家
- 🧙‍♀️ 女巫
- 🏹 猎人
- 🛡️ 守卫

### 游戏阶段
- 夜间阶段：狼人→预言家→女巫→猎人行动
- 天亮阶段：公布死亡信息
- 发言阶段：AI依次发言
- 投票阶段：投票淘汰玩家
- 胜负判定：自动判断游戏结果

### 可视化功能
- 实时显示游戏状态和主持人话术
- 玩家列表展示（存活/死亡状态）
- AI思考过程实时展示
- 支持查看玩家详细信息和操作记录
- 游戏结束后查看完整记录

## 安装运行

### 1. 克隆或下载项目

```bash
cd 狼人杀/backend
```

### 2. 安装依赖

```bash
# 使用pip安装
pip install -r requirements.txt
```

### 3. 配置环境变量（可选）

复制 `.env.example` 为 `.env` 并配置LLM API密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# LLM Provider选择 (mock, glm, openai, anthropic)
LLM_PROVIDER=glm

# GLM Configuration (智谱AI) - 推荐！
GLM_API_KEY=your_glm_api_key_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Game Configuration
DEFAULT_MODEL=glm-4-plus
GAME_SPEED=medium
```

#### 快速配置GLM模型

1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/) 注册并获取API Key
2. 在 `.env` 文件中设置 `GLM_API_KEY` 和 `LLM_PROVIDER=glm`
3. 启动游戏，在界面选择 "GLM-4/5" 作为LLM提供商

详细配置请查看 [GLM_SETUP.md](GLM_SETUP.md)

> 注意：如果不配置API密钥，系统会自动使用模拟AI，仍可正常运行游戏。

### 4. 启动服务器

#### 方式一：使用启动脚本（推荐）

```bash
chmod +x run.sh
./run.sh
```

#### 方式二：手动启动

```bash
python app.py
```

### 5. 访问游戏

打开浏览器访问：http://localhost:5000

## 使用说明

### 开始游戏
1. 选择玩家数量（6-12人）
2. 点击"开始游戏"按钮
3. 游戏将自动开始，无需人工干预

### 游戏控制
- **暂停/继续**：控制游戏流程的暂停和继续
- **重置**：重新开始一局新游戏
- **速度调节**：选择慢速/中速/快速来控制游戏节奏
- **显示/隐藏身份**：查看玩家的真实角色

### 查看详情
- 点击玩家卡片可查看详细信息、操作记录和发言记录
- 在右侧面板可以查看AI的思考过程
- 可以通过下拉筛选器查看特定玩家的思考记录

## 项目结构

```
backend/
├── app.py                 # Flask应用主文件
├── requirements.txt       # 依赖包列表
├── .env.example          # 环境变量示例
├── run.sh                # 启动脚本
├── game/                 # 游戏逻辑模块
│   ├── models.py         # 数据模型
│   ├── game_logic.py     # 游戏逻辑控制器
│   └── __init__.py
├── ai/                   # AI模块
│   ├── llm_client.py     # LLM客户端
│   ├── ai_player.py      # AI玩家逻辑
│   └── __init__.py
├── templates/            # HTML模板
│   └── index.html
└── static/               # 静态资源
    ├── css/
    │   └── style.css
    └── js/
        └── game.js
```

## 技术栈

### 后端
- **Flask**：Web框架
- **Flask-SocketIO**：WebSocket实时通信
- **OpenAI/Anthropic**：LLM API集成

### 前端
- **HTML5**：页面结构
- **CSS3**：样式设计（渐变、动画、响应式）
- **JavaScript (ES6+)**：交互逻辑
- **Socket.IO Client**：实时通信

### 游戏逻辑
- Python数据类（dataclass）
- 状态机模式管理游戏流程
- 异步处理AI决策

## 浏览器兼容性

- Chrome（推荐）
- Edge
- Firefox
- Safari

## 注意事项

1. 游戏数据仅临时存储在内存中，刷新页面会丢失进度
2. 如需使用真实LLM，请确保网络连接正常并配置正确的API密钥
3. 建议在电脑端使用，暂不支持移动端适配
4. 游戏过程中请勿频繁刷新页面

## 故障排除

### 问题：无法连接到服务器
- 检查Flask服务是否正常运行
- 确认端口5000未被占用

### 问题：Socket连接失败
- 检查浏览器控制台是否有错误信息
- 确认防火墙设置允许WebSocket连接

### 问题：AI响应很慢
- 如果使用真实LLM，检查API配额和网络延迟
- 可以切换到模拟AI模式（不配置API密钥）

## 后续扩展

- 持久化存储游戏记录
- 支持自定义角色和规则
- AI难度调节
- 多语言支持
- 移动端适配

## 许可证

本项目仅供学习和研究使用。

## 联系方式

如有问题或建议，欢迎提交Issue。
