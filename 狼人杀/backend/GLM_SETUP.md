# GLM模型配置指南

本文档介绍如何在AI机器人狼人杀项目中使用GLM（智谱AI）模型。

## 快速开始

### 1. 获取GLM API密钥

1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册账号并登录
3. 进入控制台，创建API Key
4. 复制您的API Key

### 2. 安装依赖

```bash
pip install zhipuai
```

或使用项目的依赖文件：
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件（或编辑现有文件）：

```env
# GLM Configuration (智谱AI)
GLM_API_KEY=your_glm_api_key_here

# LLM Configuration
LLM_PROVIDER=glm

# Model Configuration
DEFAULT_MODEL=glm-4-plus
```

### 4. 可用的GLM模型

| 模型名称 | 说明 | 用途 |
|---------|------|------|
| `glm-4-plus` | GLM-4 Plus | 通用对话，推荐使用 |
| `glm-4` | GLM-4 | 标准版本 |
| `glm-4-flash` | GLM-4 Flash | 快速响应 |
| `glm-4-air` | GLM-4 Air | 经济型 |
| `glm-4-long` | GLM-4 Long | 长文本 |
| `glm-3-turbo` | GLM-3 Turbo | 快速推理 |

> 注意：GLM-5如已发布，可直接替换为对应的模型名称

### 5. 启动游戏

```bash
python app.py
```

在浏览器访问：http://localhost:5000

在游戏界面选择 **GLM-4/5** 作为LLM提供商，然后开始游戏。

## 使用示例

### 直接在代码中使用

```python
from ai import LLMClient

# 使用GLM模型
llm_client = LLMClient(provider="glm", model="glm-4-plus")

response = await llm_client.generate_response(
    prompt="请扮演狼人杀中的预言家角色",
    system_prompt="你是狼人杀游戏中的预言家玩家..."
)
```

### 通过环境变量配置

```env
LLM_PROVIDER=glm
DEFAULT_MODEL=glm-4-plus
GLM_API_KEY=your_api_key_here
```

## 模型切换

在游戏界面的下拉菜单中选择不同的LLM提供商：

- **模拟AI**：不调用真实LLM，适合测试
- **GLM-4/5**：使用智谱AI模型
- **OpenAI**：使用OpenAI GPT模型
- **Anthropic**：使用Claude模型

## 故障排除

### 问题：无法连接到GLM API

**解决方案：**
1. 检查API Key是否正确
2. 确认API Key有足够的额度
3. 检查网络连接

### 问题：认证失败

**解决方案：**
1. 确认 `.env` 文件中 `GLM_API_KEY` 格式正确
2. 重启Flask服务器以加载新的环境变量

### 问题：模型响应很慢

**解决方案：**
1. 切换到 `glm-4-flash` 或 `glm-4-air` 获得更快响应
2. 调整游戏速度设置为"慢速"
3. 检查网络延迟

## API调用示例

### 聊天对话

```python
from zhipuai import ZhipuAI

client = ZhipuAI(api_key="your_api_key")

response = client.chat.completions.create(
    model="glm-4-plus",
    messages=[
        {"role": "system", "content": "你是狼人杀游戏中的预言家玩家"},
        {"role": "user", "content": "作为预言家，你应该如何发言？"}
    ],
    temperature=0.7,
    max_tokens=1000
)

print(response.choices[0].message.content)
```

## 定制角色提示词

在 `ai/ai_player.py` 中可以修改不同角色的系统提示词：

```python
def _build_system_prompt(self) -> str:
    role_name = self.player.role.value
    return f"""你是狼人杀游戏中的一名{role_name}玩家。
你需要严格遵循以下规则：
...（角色规则）
"""
```

## 性能优化建议

1. **批量请求**：多个AI玩家的请求可以并行处理
2. **缓存结果**：对于重复的场景可以缓存响应
3. **调整温度**：降低temperature参数使输出更稳定
4. **选择模型**：根据需求选择合适的模型

## 相关文档

- [智谱AI官方文档](https://open.bigmodel.cn/dev/api)
- [项目README](README.md)
- [快速启动指南](QUICKSTART.md)

## 技术支持

如遇到问题：
1. 查看智谱AI官方文档
2. 检查控制台错误信息
3. 确认API额度是否充足
