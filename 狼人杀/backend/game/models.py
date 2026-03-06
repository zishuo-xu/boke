# 游戏核心数据模型


from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from datetime import datetime


class RoleType(Enum):
    """角色类型枚举"""
    WEREWOLF = "狼人"
    VILLAGER = "村民"
    SEER = "预言家"
    WITCH = "女巫"
    HUNTER = "猎人"
    GUARD = "守卫"


class GamePhase(Enum):
    """游戏阶段枚举"""
    SETUP = "游戏设置"
    NIGHT_WEREWOLF = "狼人行动"
    NIGHT_SEER = "预言家行动"
    NIGHT_WITCH = "女巫行动"
    NIGHT_HUNTER = "猎人行动"
    DAY_ANNOUNCE = "天亮公布"
    DAY_DISCUSS = "白天发言"
    DAY_VOTE = "投票阶段"
    GAME_OVER = "游戏结束"


class PlayerStatus(Enum):
    """玩家状态枚举"""
    ALIVE = "存活"
    DEAD = "死亡"
    POISONED = "被毒杀"


@dataclass
class Player:
    """玩家数据类"""
    id: int
    name: str
    avatar: str
    role: RoleType
    status: PlayerStatus = PlayerStatus.ALIVE
    is_revealed: bool = False  # 身份是否公开
    thoughts: List[Dict] = field(default_factory=list)  # 思考记录
    actions: List[Dict] = field(default_factory=list)  # 操作记录
    speeches: List[Dict] = field(default_factory=list)  # 发言记录

    def add_thought(self, phase: str, content: str):
        """添加思考记录"""
        self.thoughts.append({
            "time": datetime.now().isoformat(),
            "phase": phase,
            "content": content
        })

    def add_action(self, phase: str, action_type: str, target_id: Optional[int] = None, result: str = ""):
        """添加操作记录"""
        self.actions.append({
            "time": datetime.now().isoformat(),
            "phase": phase,
            "action_type": action_type,
            "target_id": target_id,
            "result": result
        })

    def add_speech(self, phase: str, content: str):
        """添加发言记录"""
        self.speeches.append({
            "time": datetime.now().isoformat(),
            "phase": phase,
            "content": content
        })


@dataclass
class GameState:
    """游戏状态数据类"""
    day: int = 1
    phase: GamePhase = GamePhase.SETUP
    players: List[Player] = field(default_factory=list)
    moderator_message: str = ""
    last_night_kill: Optional[int] = None
    witch_antidote_used: bool = False
    witch_poison_used: bool = False
    witch_can_save: bool = True
    witch_can_poison: bool = True
    seer_checks: Dict[int, RoleType] = field(default_factory=dict)
    guard_protected: Optional[int] = None
    hunter_can_shoot: bool = True
    game_over: bool = False
    winner: Optional[str] = None
    current_speaker: Optional[int] = None
    vote_results: Dict[int, int] = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)

    def get_alive_players(self) -> List[Player]:
        """获取存活玩家"""
        return [p for p in self.players if p.status == PlayerStatus.ALIVE]

    def get_wolves(self) -> List[Player]:
        """获取狼人"""
        return [p for p in self.players if p.role == RoleType.WEREWOLF and p.status == PlayerStatus.ALIVE]

    def get_villagers(self) -> List[Player]:
        """获取村民"""
        return [p for p in self.players if p.role == RoleType.VILLAGER and p.status == PlayerStatus.ALIVE]

    def get_gods(self) -> List[Player]:
        """获取神职人员"""
        return [p for p in self.players if p.role in [RoleType.SEER, RoleType.WITCH, RoleType.HUNTER, RoleType.GUARD] and p.status == PlayerStatus.ALIVE]

    def check_victory(self) -> Optional[str]:
        """检查胜负条件"""
        wolves = self.get_wolves()
        villagers = self.get_villagers()
        gods = self.get_gods()

        if len(wolves) == 0:
            return "好人阵营"
        elif len(villagers) == 0 or len(gods) == 0:
            return "狼人阵营"
        elif len(wolves) >= len(villagers) + len(gods):
            return "狼人阵营"

        return None

    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """根据ID获取玩家"""
        for player in self.players:
            if player.id == player_id:
                return player
        return None

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "day": self.day,
            "phase": self.phase.value,
            "players": [
                {
                    "id": p.id,
                    "name": p.name,
                    "avatar": p.avatar,
                    "role": p.role.value,
                    "status": p.status.value,
                    "is_revealed": p.is_revealed,
                    "thoughts": p.thoughts,
                    "actions": p.actions,
                    "speeches": p.speeches
                }
                for p in self.players
            ],
            "moderator_message": self.moderator_message,
            "last_night_kill": self.last_night_kill,
            "witch_antidote_used": self.witch_antidote_used,
            "witch_poison_used": self.witch_poison_used,
            "witch_can_save": self.witch_can_save,
            "witch_can_poison": self.witch_can_poison,
            "seer_checks": self.seer_checks,
            "guard_protected": self.guard_protected,
            "hunter_can_shoot": self.hunter_can_shoot,
            "game_over": self.game_over,
            "winner": self.winner,
            "current_speaker": self.current_speaker,
            "vote_results": self.vote_results,
            "history": self.history
        }
