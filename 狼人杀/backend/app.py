# Flask应用主文件


from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import asyncio
import threading
import time
import os
import sys

# 添加当前目录到sys.path以确保模块导入正常
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game import GameLogic, GameState, GamePhase
from ai import AIOrchestrator, LLMClient

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'werewolf-game-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
CORS(app)

# 全局游戏状态
game_logic = None
ai_orchestrator = None
game_running = False
game_speed = 1.0
game_thread = None

# LLM配置
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "glm-4-plus")


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/game/start', methods=['POST'])
def start_game():
    """开始游戏"""
    global game_logic, ai_orchestrator, game_running

    data = request.get_json()
    num_players = data.get('num_players', 12)
    provider = data.get('llm_provider', LLM_PROVIDER)
    model = data.get('model', DEFAULT_MODEL)

    game_logic = GameLogic(num_players)
    game_state = game_logic.start_game(num_players)

    # 初始化AI玩家，使用配置的LLM
    llm_client = LLMClient(provider=provider, model=model) if provider != 'mock' else None
    ai_orchestrator = AIOrchestrator(llm_client=llm_client)
    ai_orchestrator.initialize_ai_players(game_state.players)

    print(f"游戏已启动 - LLM: {provider}/{model}")

    game_running = False

    # 发送初始状态
    socketio.emit('game_state', game_state.to_dict())

    return jsonify({
        'success': True,
        'game_state': game_state.to_dict(),
        'llm_config': {
            'provider': provider,
            'model': model
        }
    })


@app.route('/api/game/reset', methods=['POST'])
def reset_game():
    """重置游戏"""
    global game_logic, ai_orchestrator, game_running

    if game_logic:
        num_players = game_logic.num_players
        game_logic = GameLogic(num_players)
        game_state = game_logic.start_game(num_players)

        # 重新初始化AI玩家
        llm_client = LLMClient(provider=LLM_PROVIDER, model=DEFAULT_MODEL) if LLM_PROVIDER != 'mock' else None
        ai_orchestrator = AIOrchestrator(llm_client=llm_client)
        ai_orchestrator.initialize_ai_players(game_state.players)

        print(f"游戏已重置 - LLM: {LLM_PROVIDER}/{DEFAULT_MODEL}")

        game_running = False

        socketio.emit('game_state', game_state.to_dict())

        return jsonify({'success': True, 'game_state': game_state.to_dict()})

    return jsonify({'success': False, 'message': '游戏未开始'})


@app.route('/api/game/status', methods=['GET'])
def get_game_status():
    """获取游戏状态"""
    global game_logic

    if game_logic and game_logic.game_state:
        return jsonify({
            'success': True,
            'game_state': game_logic.game_state.to_dict()
        })

    return jsonify({'success': False, 'message': '游戏未开始'})


@app.route('/api/game/speed', methods=['POST'])
def set_game_speed():
    """设置游戏速度"""
    global game_speed

    data = request.get_json()
    speed = data.get('speed', 'medium')

    speed_map = {'slow': 2.0, 'medium': 1.0, 'fast': 0.5}
    game_speed = speed_map.get(speed, 1.0)

    socketio.emit('game_speed', {'speed': speed, 'multiplier': game_speed})

    return jsonify({'success': True, 'speed': speed})


@app.route('/api/game/control', methods=['POST'])
def control_game():
    """控制游戏（开始/暂停）"""
    global game_running, game_thread

    data = request.get_json()
    action = data.get('action', 'toggle')

    if action == 'start' and not game_running:
        game_running = True
        game_thread = threading.Thread(target=run_game_loop, daemon=True)
        game_thread.start()
        socketio.emit('game_control', {'action': 'started'})
        return jsonify({'success': True, 'action': 'started'})
    elif action == 'pause' and game_running:
        game_running = False
        socketio.emit('game_control', {'action': 'paused'})
        return jsonify({'success': True, 'action': 'paused'})
    elif action == 'toggle':
        game_running = not game_running
        if game_running:
            game_thread = threading.Thread(target=run_game_loop, daemon=True)
            game_thread.start()
        socketio.emit('game_control', {'action': 'started' if game_running else 'paused'})
        return jsonify({'success': True, 'action': 'toggled'})

    return jsonify({'success': False, 'message': '无效的操作'})


def run_game_loop():
    """游戏主循环"""
    global game_logic, ai_orchestrator, game_running, game_speed

    while game_running and game_logic and not game_logic.game_state.game_over:
        try:
            game_state = game_logic.game_state
            phase = game_state.phase

            # 等待时间（基于游戏速度）
            delay = 2.0 * game_speed
            time.sleep(delay)

            if phase == GamePhase.NIGHT_WEREWOLF:
                process_werewolf_phase(game_state)
            elif phase == GamePhase.NIGHT_SEER:
                process_seer_phase(game_state)
            elif phase == GamePhase.NIGHT_WITCH:
                process_witch_phase(game_state)
            elif phase == GamePhase.NIGHT_HUNTER:
                process_hunter_phase(game_state)
            elif phase == GamePhase.DAY_ANNOUNCE:
                game_logic.day_announce()
            elif phase == GamePhase.DAY_DISCUSS:
                process_discussion_phase(game_state)
            elif phase == GamePhase.DAY_VOTE:
                process_vote_phase(game_state)
            elif phase == GamePhase.GAME_OVER:
                game_running = False

            # 发送游戏状态更新
            socketio.emit('game_state', game_state.to_dict())

        except Exception as e:
            print(f"游戏循环错误: {e}")
            game_running = False


def process_werewolf_phase(game_state: GameState):
    """处理狼人阶段"""
    import asyncio

    async def _process():
        wolves = [p for p in game_state.get_alive_players() if p.role.value == "狼人"]
        if not wolves:
            return

        # 获取狼人的AI决策
        wolf_id = wolves[0].id
        result = await ai_orchestrator.get_ai_action(wolf_id, game_state)

        # 记录思考过程
        wolf = game_state.get_player_by_id(wolf_id)
        if wolf:
            wolf.add_thought(game_state.phase.value, result.get('thought', ''))

        # 执行狼人行动
        if result.get('target_id'):
            game_logic.werewolf_action(wolf_id, result['target_id'])

    asyncio.run(_process())


def process_seer_phase(game_state: GameState):
    """处理预言家阶段"""
    import asyncio

    async def _process():
        seers = [p for p in game_state.get_alive_players() if p.role.value == "预言家"]
        if not seers:
            return

        seer_id = seers[0].id
        result = await ai_orchestrator.get_ai_action(seer_id, game_state)

        seer = game_state.get_player_by_id(seer_id)
        if seer:
            seer.add_thought(game_state.phase.value, result.get('thought', ''))

        if result.get('target_id'):
            game_logic.seer_action(seer_id, result['target_id'])

    asyncio.run(_process())


def process_witch_phase(game_state: GameState):
    """处理女巫阶段"""
    import asyncio

    async def _process():
        witches = [p for p in game_state.get_alive_players() if p.role.value == "女巫"]
        if not witches:
            game_state.phase = GamePhase.DAY_ANNOUNCE
            return

        witch_id = witches[0].id
        result = await ai_orchestrator.get_ai_action(witch_id, game_state)

        witch = game_state.get_player_by_id(witch_id)
        if witch:
            witch.add_thought(game_state.phase.value, result.get('thought', ''))

        game_logic.witch_action(
            witch_id,
            use_antidote=result.get('use_antidote', False),
            poison_target=result.get('poison_target')
        )

    asyncio.run(_process())


def process_hunter_phase(game_state: GameState):
    """处理猎人阶段"""
    import asyncio

    async def _process():
        # 找到死亡的猎人
        dead_hunters = [p for p in game_state.players if p.role.value == "猎人" and p.status.value != "存活"]
        if not dead_hunters:
            game_state.phase = GamePhase.DAY_DISCUSS
            return

        hunter = dead_hunters[0]
        result = await ai_orchestrator.get_ai_action(hunter.id, game_state)

        hunter.add_thought(game_state.phase.value, result.get('thought', ''))

        game_logic.hunter_action(hunter.id, result.get('target_id'))

    asyncio.run(_process())


def process_discussion_phase(game_state: GameState):
    """处理发言阶段"""
    import asyncio

    async def _process():
        alive_players = game_state.get_alive_players()

        if not game_state.current_speaker:
            game_logic.start_discussion()

        current_speaker_id = game_state.current_speaker
        result = await ai_orchestrator.get_ai_action(current_speaker_id, game_state)

        speaker = game_state.get_player_by_id(current_speaker_id)
        if speaker:
            speaker.add_thought(game_state.phase.value, result.get('thought', ''))
            if result.get('speech'):
                speaker.add_speech(game_state.phase.value, result.get('speech', ''))

        game_logic.next_speaker()

    asyncio.run(_process())


def process_vote_phase(game_state: GameState):
    """处理投票阶段"""
    import asyncio

    async def _process():
        alive_players = game_state.get_alive_players()

        # 所有存活玩家投票
        for player in alive_players:
            result = await ai_orchestrator.get_ai_action(player.id, game_state)
            player.add_thought(game_state.phase.value, result.get('thought', ''))

            if result.get('target_id'):
                game_logic.vote_action(player.id, result['target_id'])

        # 统计投票结果
        game_logic.tally_votes()

    asyncio.run(_process())


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
