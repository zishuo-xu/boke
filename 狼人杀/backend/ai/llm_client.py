# LLM客户端模块


import os
from typing import Optional, Dict, Any
from openai import OpenAI
from anthropic import Anthropic
from zhipuai import ZhipuAI
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    """LLM客户端，支持OpenAI、Anthropic和GLM"""

    def __init__(self, provider: str = "openai", model: str = "gpt-3.5-turbo"):
        self.provider = provider
        self.model = model
        self.client = self._init_client()

    def _init_client(self):
        """初始化客户端"""
        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("警告：未配置OPENAI_API_KEY，将使用模拟AI")
                return None
            return OpenAI(api_key=api_key)
        elif self.provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                print("警告：未配置ANTHROPIC_API_KEY，将使用模拟AI")
                return None
            return Anthropic(api_key=api_key)
        elif self.provider == "glm":
            api_key = os.getenv("GLM_API_KEY")
            if not api_key:
                print("警告：未配置GLM_API_KEY，将使用模拟AI")
                return None
            # 使用ZhipuAI客户端
            return ZhipuAI(api_key=api_key)
        return None

    async def generate_response(self, prompt: str, system_prompt: str = "", temperature: float = 0.7) -> str:
        """生成AI响应"""
        if not self.client:
            return self._simulate_ai_response(prompt, system_prompt)

        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature
                )
                return response.choices[0].message.content
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            elif self.provider == "glm":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=1000
                )
                return response.choices[0].message.content
        except Exception as e:
            print(f"LLM调用错误: {e}")
            return self._simulate_ai_response(prompt, system_prompt)

    def _simulate_ai_response(self, prompt: str, system_prompt: str = "") -> str:
        """模拟AI响应（当没有配置API密钥时）"""
        # 简单的模拟响应，基于提示词生成一些合理的回复
        if "狼人" in prompt and "选择" in prompt:
            return "我选择一个对我威胁最大的目标。"
        elif "预言家" in prompt and "查验" in prompt:
            return "我选择一个可疑的目标进行查验。"
        elif "女巫" in prompt:
            return "根据情况，我会谨慎使用药水。"
        elif "发言" in prompt:
            return "根据目前的局势，我认为我们需要仔细分析。"
        else:
            return "我会根据游戏情况做出最合理的决策。"


class MockLLMClient:
    """模拟LLM客户端，用于测试和演示"""

    def __init__(self):
        self.werewolf_targets = []
        self.seer_checks = {}
        self.speech_templates = {
            "werewolf": [
                "我是好人，昨晚我没有杀人。",
                "我觉得{target}比较可疑，因为他表现得很紧张。",
                "我们团结起来，找出狼人！"
            ],
            "seer": [
                "我是预言家，昨晚查了{target}，他是{result}。",
                "请大家相信我，我可以验人。",
                "我有重要信息要告诉大家。"
            ],
            "witch": [
                "我是女巫，昨晚我用药了。",
                "请大家注意，我有一瓶药还没用。",
                "我会保护好人，毒死狼人。"
            ],
            "villager": [
                "我是平民，只是想找出狼人。",
                "我觉得{target}说得有道理。",
                "我们不要随便投票，要仔细分析。"
            ]
        }

    async def generate_response(self, prompt: str, system_prompt: str = "", temperature: float = 0.7) -> str:
        """生成模拟AI响应"""
        # 解析提示词以确定角色和行为
        role = self._extract_role(system_prompt)
        action = self._extract_action(prompt)

        if action == "thought":
            return self._generate_thought(role, prompt)
        elif action == "speech":
            return self._generate_speech(role, prompt)
        elif action == "vote":
            return self._generate_vote(role, prompt)
        else:
            return "我会根据游戏情况做出合理决策。"

    def _extract_role(self, system_prompt: str) -> str:
        """从系统提示词中提取角色"""
        if "狼人" in system_prompt:
            return "werewolf"
        elif "预言家" in system_prompt:
            return "seer"
        elif "女巫" in system_prompt:
            return "witch"
        elif "村民" in system_prompt:
            return "villager"
        return "villager"

    def _extract_action(self, prompt: str) -> str:
        """从提示词中提取动作类型"""
        if "思考" in prompt or "分析" in prompt:
            return "thought"
        elif "发言" in prompt:
            return "speech"
        elif "投票" in prompt:
            return "vote"
        return "action"

    def _generate_thought(self, role: str, prompt: str) -> str:
        """生成思考过程"""
        if role == "werewolf":
            return (
                "【思考过程】\n"
                "1. 当前信息：狼人阵营需要减少好人数量，但不能暴露自己。\n"
                "2. 分析：预言家和女巫是最大的威胁，应该优先解决。\n"
                "3. 决策：选择一个看起来不像预言家或女巫的好人下手。\n"
                "4. 行动：确认目标后执行袭击。"
            )
        elif role == "seer":
            return (
                "【思考过程】\n"
                "1. 当前信息：作为预言家，我的职责是验明好人身份，找出狼人。\n"
                "2. 分析：选择一个发言可疑或者行为异常的玩家查验。\n"
                "3. 决策：查验目标已确定。\n"
                "4. 策略：根据查验结果决定是否跳身份。"
            )
        elif role == "witch":
            return (
                "【思考过程】\n"
                "1. 当前信息：女巫有两瓶药，救人和毒人各一次。\n"
                "2. 分析：判断被刀者的身份，如果是重要神职可以考虑救人。\n"
                "3. 决策：根据局势决定是否使用药水。\n"
                "4. 策略：谨慎使用药水，避免浪费。"
            )
        else:
            return (
                "【思考过程】\n"
                "1. 当前信息：作为平民，我的任务是观察和投票。\n"
                "2. 分析：听取每个人的发言，找出逻辑矛盾点。\n"
                "3. 决策：根据发言和投票情况判断身份。\n"
                "4. 行动：投票给最可疑的玩家。"
            )

    def _generate_speech(self, role: str, prompt: str) -> str:
        """生成发言内容"""
        import random
        templates = self.speech_templates.get(role, self.speech_templates["villager"])
        template = random.choice(templates)
        return template.format(target="某人", result="好人" if "查了" in template else "")

    def _generate_vote(self, role: str, prompt: str) -> str:
        """生成投票决策"""
        return "【投票理由】\n根据今天的表现和发言，我认为X最可疑，所以投票给他。"
