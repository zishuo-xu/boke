# AI玩家模块


from typing import Dict, List, Optional
import random
from game.models import GameState, Player, RoleType, GamePhase
from ai.llm_client import LLMClient, MockLLMClient


class AIPlayer:
    """AI玩家类"""

    def __init__(self, player: Player, llm_client: Optional[LLMClient] = None):
        self.player = player
        self.llm_client = llm_client or MockLLMClient()
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        role_name = self.player.role.value
        return f"""你是狼人杀游戏中的一名{role_name}玩家。
你需要严格遵循以下规则：

【{role_name}规则】
{'1. 夜间与队友一起选择袭击目标。2. 白天伪装身份，引导投票指向好人。3. 保护队友，不要暴露自己。' if self.player.role == RoleType.WEREWOLF else
 '1. 夜间可以查验一名玩家的身份。2. 白天可以选择跳身份公布结果。3. 保护好人阵营，找出狼人。' if self.player.role == RoleType.SEER else
 '1. 拥有一瓶解药和一瓶毒药。2. 解药可以救活被狼人袭击的玩家，毒药可以毒死一名玩家。3. 同一晚上不能同时使用两瓶药。' if self.player.role == RoleType.WITCH else
 '1. 被投票出局或被刀时可以选择开枪带走一名玩家。2. 开枪是被动技能，被淘汰后决定是否使用。' if self.player.role == RoleType.HUNTER else
 '1. 没有特殊技能，依靠观察和推理。2. 发言和投票是唯一的武器。3. 保护好人阵营，找出狼人。'}

【行为要求】
1. 生成思考过程时，要包含：已知信息、自身定位、决策分析、最终决定。
2. 发言要符合角色立场，逻辑连贯。
3. 不要作弊，基于公开信息做决策。
4. 语言要自然，模拟真实玩家的思考方式。
"""

    async def think_and_act(self, game_state: GameState, phase: GamePhase) -> Dict:
        """根据游戏阶段进行思考和行动"""
        self.system_prompt = self._build_system_prompt()

        if phase == GamePhase.NIGHT_WEREWOLF and self.player.role == RoleType.WEREWOLF:
            return await self._werewolf_night_action(game_state)
        elif phase == GamePhase.NIGHT_SEER and self.player.role == RoleType.SEER:
            return await self._seer_night_action(game_state)
        elif phase == GamePhase.NIGHT_WITCH and self.player.role == RoleType.WITCH:
            return await self._witch_night_action(game_state)
        elif phase == GamePhase.NIGHT_HUNTER and self.player.role == RoleType.HUNTER:
            return await self._hunter_action(game_state)
        elif phase == GamePhase.DAY_DISCUSS:
            return await self._day_speech(game_state)
        elif phase == GamePhase.DAY_VOTE:
            return await self._vote_action(game_state)

        return {"action": None, "thought": "", "speech": ""}

    async def _werewolf_night_action(self, game_state: GameState) -> Dict:
        """狼人夜间行动"""
        alive_players = [p for p in game_state.players if p.status.value == "存活" and p.id != self.player.id]

        prompt = f"""现在是狼人夜间行动阶段。
你的队友有：{', '.join([p.name for p in alive_players if p.role == RoleType.WEREWOLF])}。
可以选择袭击的目标：{', '.join([p.name for p in alive_players if p.role != RoleType.WEREWOLF])}。

请分析并选择袭击目标。"""

        thought = await self.llm_client.generate_response(
            prompt=f"【思考】{prompt}\n\n请生成你的思考过程。",
            system_prompt=self.system_prompt
        )

        # 简单的目标选择逻辑
        if alive_players:
            target = random.choice([p for p in alive_players if p.role != RoleType.WEREWOLF])
            if not target:
                target = random.choice(alive_players)
        else:
            target = None

        return {
            "action": "werewolf_kill",
            "target_id": target.id if target else None,
            "thought": thought,
            "speech": ""
        }

    async def _seer_night_action(self, game_state: GameState) -> Dict:
        """预言家夜间行动"""
        alive_players = [p for p in game_state.players if p.status.value == "存活" and p.id != self.player.id]

        prompt = f"""现在是预言家夜间行动阶段。
可以查验的玩家：{', '.join([p.name for p in alive_players])}。

请选择要查验的目标。"""

        thought = await self.llm_client.generate_response(
            prompt=f"【思考】{prompt}\n\n请生成你的思考过程。",
            system_prompt=self.system_prompt
        )

        if alive_players:
            target = random.choice([p for p in alive_players if p.id not in game_state.seer_checks])
            if not target or len(game_state.seer_checks) >= len(alive_players):
                target = random.choice(alive_players)
        else:
            target = None

        return {
            "action": "seer_check",
            "target_id": target.id if target else None,
            "thought": thought,
            "speech": ""
        }

    async def _witch_night_action(self, game_state: GameState) -> Dict:
        """女巫夜间行动"""
        can_save = game_state.witch_can_save
        can_poison = game_state.witch_can_poison

        target_name = ""
        if game_state.last_night_kill:
            target = game_state.get_player_by_id(game_state.last_night_kill)
            if target:
                target_name = target.name

        alive_players = [p for p in game_state.players if p.status.value == "存活" and p.id != self.player.id]

        prompt = f"""现在是女巫夜间行动阶段。
昨晚被袭击的玩家：{target_name or '无'}
剩余解药：{'是' if can_save else '否'}
剩余毒药：{'是' if can_poison else '否'}
可以毒的玩家：{', '.join([p.name for p in alive_players])}

请决定是否使用解药或毒药。"""

        thought = await self.llm_client.generate_response(
            prompt=f"【思考】{prompt}\n\n请生成你的思考过程。",
            system_prompt=self.system_prompt
        )

        use_antidote = can_save and random.choice([True, False])
        poison_target = None

        if can_poison and not use_antidote and alive_players:
            poison_target = random.choice(alive_players).id

        return {
            "action": "witch_action",
            "use_antidote": use_antidote,
            "poison_target": poison_target,
            "thought": thought,
            "speech": ""
        }

    async def _hunter_action(self, game_state: GameState) -> Dict:
        """猎人行动"""
        alive_players = [p for p in game_state.players if p.status.value == "存活"]

        prompt = f"""你作为猎人已经被淘汰，可以选择开枪带走一名玩家。
可以开枪的玩家：{', '.join([p.name for p in alive_players])}

请决定是否开枪以及选择目标。"""

        thought = await self.llm_client.generate_response(
            prompt=f"【思考】{prompt}\n\n请生成你的思考过程。",
            system_prompt=self.system_prompt
        )

        should_shoot = random.choice([True, False])
        target_id = None

        if should_shoot and alive_players:
            target_id = random.choice(alive_players).id

        return {
            "action": "hunter_shoot",
            "target_id": target_id,
            "thought": thought,
            "speech": ""
        }

    async def _day_speech(self, game_state: GameState) -> Dict:
        """白天发言"""
        alive_players = game_state.get_alive_players()
        dead_players = [p for p in game_state.players if p.status.value != "存活"]

        game_info = f"游戏进行到第{game_state.day}天。"
        game_info += f"存活玩家：{', '.join([p.name for p in alive_players])}。"
        if dead_players:
            game_info += f"已死亡玩家：{', '.join([p.name for p in dead_players])}。"

        prompt = f"""现在是白天发言阶段。
{game_info}

请根据当前局势发表你的观点（作为{self.player.role.value}）。"""

        thought = await self.llm_client.generate_response(
            prompt=f"【思考】{prompt}\n\n请生成你的发言思考过程。",
            system_prompt=self.system_prompt
        )

        speech = await self.llm_client.generate_response(
            prompt=f"【发言】{prompt}\n\n请生成你的发言内容。",
            system_prompt=self.system_prompt
        )

        return {
            "action": "speech",
            "target_id": None,
            "thought": thought,
            "speech": speech
        }

    async def _vote_action(self, game_state: GameState) -> Dict:
        """投票行动"""
        alive_players = [p for p in game_state.players if p.status.value == "存活" and p.id != self.player.id]

        prompt = f"""现在是投票阶段。
可以投票的玩家：{', '.join([p.name for p in alive_players])}

请决定你的投票目标。"""

        thought = await self.llm_client.generate_response(
            prompt=f"【思考】{prompt}\n\n请生成你的投票思考过程。",
            system_prompt=self.system_prompt
        )

        target_id = None
        if alive_players:
            target_id = random.choice(alive_players).id

        return {
            "action": "vote",
            "target_id": target_id,
            "thought": thought,
            "speech": ""
        }


class AIOrchestrator:
    """AI编排器，管理所有AI玩家"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client
        self.ai_players: Dict[int, AIPlayer] = {}

    def initialize_ai_players(self, players: List[Player]):
        """初始化AI玩家"""
        self.ai_players = {}
        for player in players:
            self.ai_players[player.id] = AIPlayer(player, self.llm_client)

    async def get_ai_action(self, player_id: int, game_state: GameState) -> Dict:
        """获取AI玩家的行动"""
        ai_player = self.ai_players.get(player_id)
        if not ai_player:
            return {"action": None, "thought": "", "speech": ""}

        return await ai_player.think_and_act(game_state, game_state.phase)
