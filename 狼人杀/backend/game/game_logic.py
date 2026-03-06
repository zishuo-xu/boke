# 游戏逻辑控制模块


from .models import GameState, Player, RoleType, GamePhase, PlayerStatus
from typing import List, Optional, Tuple
import random


class GameLogic:
    """游戏逻辑控制器"""

    def __init__(self, num_players: int = 12):
        self.num_players = num_players
        self.game_state: Optional[GameState] = None
        self.avatars = self._generate_avatars()
        self.names = self._generate_names()

    def _generate_avatars(self) -> List[str]:
        """生成头像列表"""
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
                  '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
                  '#F8B739', '#52B788']
        return colors

    def _generate_names(self) -> List[str]:
        """生成玩家名称"""
        names = [
            "小明", "小红", "小华", "小李", "小张", "小王",
            "小赵", "小钱", "小孙", "小周", "小吴", "小郑"
        ]
        return names[:self.num_players]

    def _distribute_roles(self) -> List[RoleType]:
        """根据玩家数量分配角色"""
        roles = []

        if self.num_players == 6:
            roles = [RoleType.WEREWOLF, RoleType.WEREWOLF, RoleType.SEER,
                    RoleType.WITCH, RoleType.VILLAGER, RoleType.VILLAGER]
        elif self.num_players == 8:
            roles = [RoleType.WEREWOLF, RoleType.WEREWOLF, RoleType.SEER,
                    RoleType.WITCH, RoleType.HUNTER, RoleType.VILLAGER,
                    RoleType.VILLAGER, RoleType.VILLAGER]
        elif self.num_players == 9:
            roles = [RoleType.WEREWOLF, RoleType.WEREWOLF, RoleType.WEREWOLF,
                    RoleType.SEER, RoleType.WITCH, RoleType.HUNTER,
                    RoleType.VILLAGER, RoleType.VILLAGER, RoleType.VILLAGER]
        elif self.num_players == 10:
            roles = [RoleType.WEREWOLF, RoleType.WEREWOLF, RoleType.WEREWOLF,
                    RoleType.SEER, RoleType.WITCH, RoleType.HUNTER,
                    RoleType.GUARD, RoleType.VILLAGER, RoleType.VILLAGER,
                    RoleType.VILLAGER]
        elif self.num_players == 12:
            roles = [RoleType.WEREWOLF, RoleType.WEREWOLF, RoleType.WEREWOLF, RoleType.WEREWOLF,
                    RoleType.SEER, RoleType.WITCH, RoleType.HUNTER, RoleType.GUARD,
                    RoleType.VILLAGER, RoleType.VILLAGER, RoleType.VILLAGER, RoleType.VILLAGER]
        else:
            # 默认12人配置
            roles = [RoleType.WEREWOLF, RoleType.WEREWOLF, RoleType.WEREWOLF, RoleType.WEREWOLF,
                    RoleType.SEER, RoleType.WITCH, RoleType.HUNTER, RoleType.GUARD,
                    RoleType.VILLAGER, RoleType.VILLAGER, RoleType.VILLAGER, RoleType.VILLAGER]

        return roles

    def start_game(self, num_players: int = 12) -> GameState:
        """开始新游戏"""
        self.num_players = num_players
        self.game_state = GameState()

        # 分配角色
        roles = self._distribute_roles()
        random.shuffle(roles)

        # 创建玩家
        for i in range(self.num_players):
            player = Player(
                id=i + 1,
                name=self.names[i],
                avatar=self.avatars[i % len(self.avatars)],
                role=roles[i],
                status=PlayerStatus.ALIVE
            )
            self.game_state.players.append(player)

        # 初始化主持人话术
        self.game_state.moderator_message = (
            f"欢迎来到AI机器人狼人杀游戏！\n\n"
            f"本局游戏共有{self.num_players}名玩家参与，角色分配如下：\n"
            f"狼人：{len([r for r in roles if r == RoleType.WEREWOLF])}人\n"
            f"神职：{len([r for r in roles if r in [RoleType.SEER, RoleType.WITCH, RoleType.HUNTER, RoleType.GUARD]])}人\n"
            f"平民：{len([r for r in roles if r == RoleType.VILLAGER])}人\n\n"
            f"游戏即将开始，请各位AI机器人查看自己的角色。"
        )

        return self.game_state

    def start_night_phase(self) -> GameState:
        """开始夜间阶段"""
        self.game_state.phase = GamePhase.NIGHT_WEREWOLF
        self.game_state.moderator_message = (
            f"【第{self.game_state.day}夜】\n\n"
            f"天黑请闭眼...\n\n"
            f"狼人请睁眼，请选择今晚要袭击的目标。"
        )
        return self.game_state

    def werewolf_action(self, player_id: int, target_id: int) -> GameState:
        """狼人行动"""
        player = self.game_state.get_player_by_id(player_id)
        target = self.game_state.get_player_by_id(target_id)

        if player and target:
            self.game_state.last_night_kill = target_id
            self.game_state.moderator_message = (
                f"狼人已选择目标，请闭眼。\n\n"
                f"预言家请睁眼，请选择今晚要查验的目标。"
            )
            self.game_state.phase = GamePhase.NIGHT_SEER

        return self.game_state

    def seer_action(self, player_id: int, target_id: int) -> GameState:
        """预言家行动"""
        player = self.game_state.get_player_by_id(player_id)
        target = self.game_state.get_player_by_id(target_id)

        if player and target:
            self.game_state.seer_checks[target_id] = target.role
            self.game_state.moderator_message = (
                f"预言家已查验完毕，请闭眼。\n\n"
                f"女巫请睁眼，今晚{target.name}被狼人袭击，是否使用解药？"
            )
            self.game_state.phase = GamePhase.NIGHT_WITCH

        return self.game_state

    def witch_action(self, player_id: int, use_antidote: bool = False, poison_target: Optional[int] = None) -> GameState:
        """女巫行动"""
        player = self.game_state.get_player_by_id(player_id)

        if player:
            if use_antidote and self.game_state.witch_can_save:
                self.game_state.last_night_kill = None
                self.game_state.witch_antidote_used = True
                self.game_state.witch_can_save = False

            if poison_target and self.game_state.witch_can_poison and not use_antidote:
                target = self.game_state.get_player_by_id(poison_target)
                if target:
                    target.status = PlayerStatus.POISONED
                    self.game_state.witch_poison_used = True
                    self.game_state.witch_can_poison = False

            self.game_state.moderator_message = "女巫已行动完毕，请闭眼。\n\n天亮了！"
            self.game_state.phase = GamePhase.DAY_ANNOUNCE

        return self.game_state

    def day_announce(self) -> GameState:
        """天亮公布死亡信息"""
        deaths = []

        # 检查狼人击杀
        if self.game_state.last_night_kill:
            target = self.game_state.get_player_by_id(self.game_state.last_night_kill)
            if target:
                target.status = PlayerStatus.DEAD
                deaths.append(target.name)

        # 检查被毒杀的玩家
        for player in self.game_state.players:
            if player.status == PlayerStatus.POISONED:
                deaths.append(player.name)

        if deaths:
            self.game_state.moderator_message = (
                f"【第{self.game_state.day}天】\n\n"
                f"昨晚，{', '.join(deaths)}倒在了血泊中，请发表遗言。"
            )

            # 检查是否需要猎人开枪
            for player in deaths:
                if player.role == RoleType.HUNTER and self.game_state.hunter_can_shoot:
                    self.game_state.phase = GamePhase.NIGHT_HUNTER
                    return self.game_state
        else:
            self.game_state.moderator_message = (
                f"【第{self.game_state.day}天】\n\n"
                f"昨晚是平安夜，没有人死亡。"
            )

        self.game_state.phase = GamePhase.DAY_DISCUSS

        return self.game_state

    def hunter_action(self, player_id: int, target_id: Optional[int] = None) -> GameState:
        """猎人行动"""
        if target_id:
            target = self.game_state.get_player_by_id(target_id)
            if target:
                target.status = PlayerStatus.DEAD
                self.game_state.moderator_message = f"猎人开枪带走了{target.name}。"
        else:
            self.game_state.moderator_message = "猎人选择不开枪。"

        self.game_state.hunter_can_shoot = False
        self.game_state.phase = GamePhase.DAY_DISCUSS
        return self.game_state

    def start_discussion(self) -> GameState:
        """开始发言阶段"""
        alive_players = self.game_state.get_alive_players()
        self.game_state.moderator_message = (
            f"现在开始发言环节，请按照以下顺序依次发言：\n\n"
            f"{' -> '.join([p.name for p in alive_players])}\n\n"
            f"首先由{alive_players[0].name}开始发言。"
        )
        self.game_state.current_speaker = alive_players[0].id
        return self.game_state

    def next_speaker(self) -> GameState:
        """下一位发言者"""
        alive_players = self.game_state.get_alive_players()
        if not alive_players:
            return self.game_state

        current_idx = -1
        for i, player in enumerate(alive_players):
            if player.id == self.game_state.current_speaker:
                current_idx = i
                break

        if current_idx < len(alive_players) - 1:
            self.game_state.current_speaker = alive_players[current_idx + 1].id
            next_player = alive_players[current_idx + 1]
            self.game_state.moderator_message = f"请{next_player.name}发言。"
        else:
            self.game_state.phase = GamePhase.DAY_VOTE
            self.game_state.moderator_message = "发言结束，现在开始投票阶段！"

        return self.game_state

    def vote_action(self, player_id: int, target_id: int) -> GameState:
        """投票行动"""
        if target_id not in self.game_state.vote_results:
            self.game_state.vote_results[target_id] = 0
        self.game_state.vote_results[target_id] += 1

        return self.game_state

    def tally_votes(self) -> GameState:
        """统计投票结果"""
        if not self.game_state.vote_results:
            self.game_state.moderator_message = "本轮无人投票，平票。"
        else:
            max_votes = max(self.game_state.vote_results.values())
            eliminated = [pid for pid, votes in self.game_state.vote_results.items() if votes == max_votes]

            if len(eliminated) == 1:
                player = self.game_state.get_player_by_id(eliminated[0])
                if player:
                    player.status = PlayerStatus.DEAD
                    player.is_revealed = True

                    self.game_state.moderator_message = (
                        f"投票结果：{player.name}被投票出局，身份是【{player.role.value}】。"
                    )

                    # 检查猎人
                    if player.role == RoleType.HUNTER and self.game_state.hunter_can_shoot:
                        self.game_state.phase = GamePhase.NIGHT_HUNTER
                        return self.game_state
            else:
                names = [self.game_state.get_player_by_id(pid).name for pid in eliminated]
                self.game_state.moderator_message = f"平票：{', '.join(names)}得票相同，无人出局。"

        # 检查胜负
        winner = self.game_state.check_victory()
        if winner:
            self.game_state.game_over = True
            self.game_state.winner = winner
            self.game_state.phase = GamePhase.GAME_OVER
            self._reveal_all_roles()
        else:
            self.game_state.day += 1
            self.game_state.vote_results = {}
            self.game_state.guard_protected = None
            self._start_next_night()

        return self.game_state

    def _reveal_all_roles(self):
        """公布所有角色"""
        for player in self.game_state.players:
            player.is_revealed = True

        self.game_state.moderator_message = (
            f"游戏结束！\n\n"
            f"获胜阵营：【{self.game_state.winner}】\n\n"
            f"所有玩家身份：\n" +
            "\n".join([f"{p.name}：{p.role.value}" for p in self.game_state.players])
        )

    def _start_next_night(self):
        """开始下一夜"""
        self.game_state.phase = GamePhase.NIGHT_WEREWOLF
        self.game_state.moderator_message = (
            f"【第{self.game_state.day}夜】\n\n"
            f"天黑请闭眼...\n\n"
            f"狼人请睁眼，请选择今晚要袭击的目标。"
        )

    def reset_game(self) -> GameState:
        """重置游戏"""
        return self.start_game(self.num_players)
