#!/usr/bin/env python3
"""
GLM模型测试脚本
用于验证GLM API配置是否正确
"""

import os
import asyncio
from dotenv import load_dotenv
from ai import LLMClient

# 加载环境变量
load_dotenv()


async def test_glm():
    """测试GLM模型连接"""
    print("=" * 60)
    print("  GLM模型测试")
    print("=" * 60)

    # 检查API密钥
    api_key = os.getenv("GLM_API_KEY")
    if not api_key:
        print("❌ 错误：未配置GLM_API_KEY")
        print("请在.env文件中设置：GLM_API_KEY=your_api_key")
        return

    print(f"✓ API密钥已配置: {api_key[:10]}...")

    # 创建GLM客户端
    print("\n正在初始化GLM客户端...")
    llm_client = LLMClient(provider="glm", model="glm-4-plus")

    if not llm_client.client:
        print("❌ 错误：无法创建GLM客户端")
        return

    print("✓ GLM客户端创建成功")

    # 测试简单对话
    print("\n测试1: 简单问答")
    print("-" * 60)
    try:
        response = await llm_client.generate_response(
            prompt="你好，请用一句话介绍你自己。",
            system_prompt="你是一个友好的AI助手。",
            temperature=0.7
        )
        print(f"✓ 响应: {response}")
    except Exception as e:
        print(f"❌ 错误: {e}")
        return

    # 测试狼人杀角色扮演
    print("\n测试2: 狼人杀角色扮演（预言家）")
    print("-" * 60)
    try:
        response = await llm_client.generate_response(
            prompt="作为预言家，你应该如何在第一天发言？",
            system_prompt="""你是狼人杀游戏中的预言家玩家。
你的职责：
1. 夜间可以查验一名玩家的身份
2. 白天可以选择是否跳预言家身份
3. 保护好人阵营，找出狼人
请用简短、有力的语言回复。""",
            temperature=0.7
        )
        print(f"✓ 预言家发言:\n{response}")
    except Exception as e:
        print(f"❌ 错误: {e}")
        return

    # 测试思考过程生成
    print("\n测试3: 生成思考过程")
    print("-" * 60)
    try:
        response = await llm_client.generate_response(
            prompt="现在是狼人夜间行动阶段。请生成你的思考过程，包括：1.当前信息 2.分析 3.决策 4.行动。",
            system_prompt="你是狼人杀游戏中的狼人玩家。你需要选择一个目标进行袭击。",
            temperature=0.7
        )
        print(f"✓ 思考过程:\n{response}")
    except Exception as e:
        print(f"❌ 错误: {e}")
        return

    print("\n" + "=" * 60)
    print("✓ 所有测试通过！GLM配置正常")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_glm())
