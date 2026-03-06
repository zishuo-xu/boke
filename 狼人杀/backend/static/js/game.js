// AI机器人狼人杀 - 主JavaScript文件


class WerewolfGame {
    constructor() {
        this.socket = null;
        this.gameState = null;
        this.showRoles = false;
        this.selectedPlayer = null;
        this.gameRunning = false;
        this.typewriterInterval = null;

        this.init();
    }

    init() {
        this.initSocket();
        this.initEventListeners();
        this.loadInitialUI();
    }

    initSocket() {
        this.socket = io();

        this.socket.on('connect', () => {
            console.log('已连接到服务器');
        });

        this.socket.on('game_state', (data) => {
            this.updateGameState(data);
        });

        this.socket.on('game_speed', (data) => {
            this.updateSpeedDisplay(data);
        });

        this.socket.on('game_control', (data) => {
            this.handleGameControl(data);
        });

        this.socket.on('disconnect', () => {
            console.log('与服务器的连接已断开');
        });
    }

    initEventListeners() {
        console.log('初始化事件监听器...');

        // 开始游戏按钮
        const startButton = document.getElementById('startGame');
        console.log('开始按钮元素:', startButton);

        if (startButton) {
            startButton.addEventListener('click', () => {
                console.log('开始游戏按钮被点击！');
                this.startGame();
            });
            console.log('开始游戏按钮事件监听器已绑定');
        } else {
            console.error('未找到开始游戏按钮！');
        }

        // 暂停游戏按钮
        document.getElementById('pauseGame').addEventListener('click', () => {
            this.pauseGame();
        });

        // 重置游戏按钮
        document.getElementById('resetGame').addEventListener('click', () => {
            this.resetGame();
        });

        // 速度控制
        document.getElementById('speedControl').addEventListener('change', (e) => {
            this.setSpeed(e.target.value);
        });

        // 显示/隐藏角色
        document.getElementById('toggleRoles').addEventListener('click', () => {
            this.toggleRoles();
        });

        // 玩家筛选
        document.getElementById('playerFilter').addEventListener('change', (e) => {
            this.filterThoughts(e.target.value);
        });

        // 关闭弹窗
        document.getElementById('closeModal').addEventListener('click', () => {
            this.closeModal();
        });

        // 点击弹窗外部关闭
        document.getElementById('playerModal').addEventListener('click', (e) => {
            if (e.target.id === 'playerModal') {
                this.closeModal();
            }
        });
    }

    loadInitialUI() {
        // 初始化UI状态
        this.updatePhaseDisplay('等待开始', '🎮');
        this.updateDayCounter(1);
    }

    async startGame() {
        console.log('=== 开始游戏方法被调用 ===');

        const numPlayers = parseInt(document.getElementById('playerCount').value);
        const llmProvider = document.getElementById('llmProvider').value;

        console.log('配置:', { numPlayers, llmProvider });

        // 根据provider选择模型
        let model = 'glm-4-plus';
        if (llmProvider === 'glm') {
            model = 'glm-4-plus'; // 或使用 'glm-5' 如果API支持
        } else if (llmProvider === 'openai') {
            model = 'gpt-3.5-turbo';
        } else if (llmProvider === 'anthropic') {
            model = 'claude-3-haiku-20240307';
        }

        try {
            const response = await fetch('/api/game/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    num_players: numPlayers,
                    llm_provider: llmProvider,
                    model: model
                })
            });

            const data = await response.json();

            if (data.success) {
                this.gameState = data.game_state;
                this.updateAllUI();
                this.startAutoPlay();

                document.getElementById('startGame').textContent = '游戏中...';
                document.getElementById('startGame').disabled = true;
                document.getElementById('pauseGame').disabled = false;

                console.log('LLM配置:', data.llm_config);
            }
        } catch (error) {
            console.error('开始游戏失败:', error);
            alert('开始游戏失败，请检查服务器连接');
        }
    }

    async pauseGame() {
        try {
            const response = await fetch('/api/game/control', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'toggle' })
            });

            const data = await response.json();

            if (data.success) {
                this.gameRunning = !this.gameRunning;
                document.getElementById('pauseGame').textContent =
                    this.gameRunning ? '暂停' : '继续';
            }
        } catch (error) {
            console.error('控制游戏失败:', error);
        }
    }

    async resetGame() {
        if (!confirm('确定要重置游戏吗？当前进度将丢失。')) {
            return;
        }

        try {
            const response = await fetch('/api/game/reset', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const data = await response.json();

            if (data.success) {
                this.gameState = data.game_state;
                this.updateAllUI();
                this.gameRunning = false;

                document.getElementById('startGame').textContent = '开始游戏';
                document.getElementById('startGame').disabled = false;
                document.getElementById('pauseGame').textContent = '暂停';
                document.getElementById('pauseGame').disabled = true;
            }
        } catch (error) {
            console.error('重置游戏失败:', error);
        }
    }

    async setSpeed(speed) {
        try {
            const response = await fetch('/api/game/speed', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ speed: speed })
            });

            const data = await response.json();

            if (data.success) {
                this.updateSpeedDisplay({ speed: speed });
            }
        } catch (error) {
            console.error('设置速度失败:', error);
        }
    }

    startAutoPlay() {
        // 自动开始游戏流程
        fetch('/api/game/control', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'start' })
        });
    }

    updateGameState(data) {
        this.gameState = data;
        this.updateAllUI();
    }

    updateAllUI() {
        if (!this.gameState) return;

        this.updatePlayersGrid();
        this.updateModeratorMessage();
        this.updatePhaseDisplay();
        this.updateDayCounter();
        this.updateStatusFooter();
        this.updateThoughtsPanel();
        this.updatePlayerFilter();
        this.updateGameScene();

        // 检查游戏是否结束
        if (this.gameState.game_over) {
            this.showRoles = true;
            document.getElementById('startGame').disabled = false;
            document.getElementById('startGame').textContent = '新游戏';
            document.getElementById('pauseGame').disabled = true;
        }
    }

    updatePlayersGrid() {
        const grid = document.getElementById('playersGrid');
        grid.innerHTML = '';

        this.gameState.players.forEach(player => {
            const card = document.createElement('div');
            card.className = `player-card ${player.status === '存活' ? 'alive' : 'dead'}`;
            card.style.borderLeftColor = player.avatar;

            if (this.gameState.current_speaker === player.id) {
                card.classList.add('current-speaker');
            }

            card.innerHTML = `
                <div class="player-avatar" style="background: ${player.avatar}">
                    ${player.name.charAt(0)}
                </div>
                <div class="player-name">${player.name}</div>
                <div class="player-role ${this.showRoles || player.is_revealed ? 'revealed' : ''}">
                    ${player.role}
                </div>
                <div class="player-status">
                    <span class="status-badge ${player.status === '存活' ? 'alive' : 'dead'}">
                        ${player.status}
                    </span>
                </div>
            `;

            card.addEventListener('click', () => {
                this.showPlayerDetails(player);
            });

            grid.appendChild(card);
        });
    }

    updateModeratorMessage() {
        const message = document.getElementById('moderatorMessage');
        this.typewriterEffect(message, this.gameState.moderator_message || '');
    }

    typewriterEffect(element, text) {
        if (this.typewriterInterval) {
            clearInterval(this.typewriterInterval);
        }

        element.textContent = '';
        let index = 0;

        this.typewriterInterval = setInterval(() => {
            if (index < text.length) {
                element.textContent += text.charAt(index);
                index++;
            } else {
                clearInterval(this.typewriterInterval);
            }
        }, 30);
    }

    updatePhaseDisplay(phase, icon) {
        const phaseText = document.getElementById('phaseText');
        const phaseIndicator = document.getElementById('phaseIndicator');

        if (phase) {
            phaseText.textContent = phase;
        } else if (this.gameState) {
            phaseText.textContent = this.gameState.phase || '等待开始';
        }

        if (icon) {
            phaseIndicator.querySelector('.phase-icon').textContent = icon;
        }
    }

    updateDayCounter(day) {
        const dayCounter = document.getElementById('dayCounter');
        if (day) {
            dayCounter.textContent = `第 ${day} 天`;
        } else if (this.gameState) {
            dayCounter.textContent = `第 ${this.gameState.day} 天`;
        }
    }

    updateStatusFooter() {
        if (!this.gameState) return;

        const gameStatus = document.getElementById('gameStatus');
        const aliveCount = document.getElementById('aliveCount');

        const alivePlayers = this.gameState.players.filter(p => p.status === '存活');
        aliveCount.textContent = `${alivePlayers.length} / ${this.gameState.players.length}`;

        if (this.gameState.game_over) {
            gameStatus.textContent = '游戏结束';
            gameStatus.style.color = 'var(--accent-color)';
        } else if (this.gameState.phase === '游戏设置') {
            gameStatus.textContent = '准备中';
            gameStatus.style.color = 'var(--warning-color)';
        } else {
            gameStatus.textContent = '进行中';
            gameStatus.style.color = 'var(--success-color)';
        }
    }

    updateThoughtsPanel() {
        if (!this.gameState) return;

        const thoughtsList = document.getElementById('thoughtsList');
        thoughtsList.innerHTML = '';

        const filterValue = document.getElementById('playerFilter').value;

        // 收集所有思考记录
        const allThoughts = [];

        this.gameState.players.forEach(player => {
            player.thoughts.forEach(thought => {
                if (filterValue === 'all' || filterValue === player.name) {
                    allThoughts.push({
                        player: player.name,
                        ...thought
                    });
                }
            });
        });

        // 按时间排序（最新的在前面）
        allThoughts.sort((a, b) => new Date(b.time) - new Date(a.time));

        if (allThoughts.length === 0) {
            thoughtsList.innerHTML = `
                <div class="thought-placeholder">
                    <p>AI的思考过程将在这里显示</p>
                </div>
            `;
            return;
        }

        allThoughts.forEach(thought => {
            const thoughtItem = document.createElement('div');
            thoughtItem.className = 'thought-item';

            const time = new Date(thought.time);
            const timeStr = time.toLocaleTimeString('zh-CN', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });

            thoughtItem.innerHTML = `
                <div class="thought-header">
                    <span class="thought-player">${thought.player}</span>
                    <span class="thought-phase">${thought.phase}</span>
                    <span class="thought-time">${timeStr}</span>
                </div>
                <div class="thought-content">${thought.content}</div>
            `;

            thoughtsList.appendChild(thoughtItem);
        });
    }

    updatePlayerFilter() {
        const filter = document.getElementById('playerFilter');
        const currentValue = filter.value;

        // 保存当前选择
        filter.innerHTML = '<option value="all">显示全部</option>';

        if (this.gameState) {
            this.gameState.players.forEach(player => {
                const option = document.createElement('option');
                option.value = player.name;
                option.textContent = player.name;
                filter.appendChild(option);
            });

            // 恢复选择
            if (currentValue) {
                filter.value = currentValue;
            }
        }
    }

    updateGameScene() {
        const scene = document.getElementById('gameScene');

        if (this.gameState.game_over) {
            scene.innerHTML = `
                <div class="scene-placeholder animate-fade-in">
                    <div class="placeholder-icon">🏆</div>
                    <h2 style="color: var(--accent-color); font-size: 24px; margin: 16px 0;">
                        游戏结束！${this.gameState.winner}获胜！
                    </h2>
                    <p style="font-size: 16px;">点击"开始游戏"开始新一局</p>
                </div>
            `;
        } else if (this.gameState.phase.includes('夜间')) {
            scene.innerHTML = `
                <div class="scene-placeholder animate-fade-in">
                    <div class="placeholder-icon">🌙</div>
                    <p>夜间阶段...请关注主持人消息</p>
                </div>
            `;
        } else if (this.gameState.phase.includes('天亮') || this.gameState.phase.includes('发言')) {
            scene.innerHTML = `
                <div class="scene-placeholder animate-fade-in">
                    <div class="placeholder-icon">☀️</div>
                    <p>白天阶段...请关注发言</p>
                </div>
            `;
        } else if (this.gameState.phase.includes('投票')) {
            scene.innerHTML = `
                <div class="scene-placeholder animate-fade-in">
                    <div class="placeholder-icon">🗳️</div>
                    <p>投票阶段...请关注投票结果</p>
                </div>
            `;
        }
    }

    updateSpeedDisplay(data) {
        const currentSpeed = document.getElementById('currentSpeed');
        const speedText = {
            'slow': '慢速',
            'medium': '中速',
            'fast': '快速'
        };
        currentSpeed.textContent = speedText[data.speed] || '中速';
    }

    handleGameControl(data) {
        if (data.action === 'started') {
            this.gameRunning = true;
            document.getElementById('pauseGame').textContent = '暂停';
        } else if (data.action === 'paused') {
            this.gameRunning = false;
            document.getElementById('pauseGame').textContent = '继续';
        }
    }

    toggleRoles() {
        this.showRoles = !this.showRoles;
        const btn = document.getElementById('toggleRoles');
        btn.textContent = this.showRoles ? '隐藏身份' : '显示身份';
        this.updatePlayersGrid();
    }

    filterThoughts(playerName) {
        this.updateThoughtsPanel();
    }

    showPlayerDetails(player) {
        const modal = document.getElementById('playerModal');
        const modalBody = document.getElementById('modalBody');
        const modalTitle = document.getElementById('modalPlayerName');

        modalTitle.textContent = `${player.name} - 详细信息`;

        const actionsHtml = player.actions.length > 0
            ? `<h3 style="margin: 16px 0 12px;">操作记录</h3>
               <ul style="padding-left: 20px;">
                   ${player.actions.map(action => `
                       <li style="margin-bottom: 8px;">
                           <strong>${action.phase}</strong>: ${action.action_type}
                           ${action.result ? ` - ${action.result}` : ''}
                       </li>
                   `).join('')}
               </ul>`
            : '<p style="color: #7f8c8d;">暂无操作记录</p>';

        const speechesHtml = player.speeches.length > 0
            ? `<h3 style="margin: 16px 0 12px;">发言记录</h3>
               <div style="background: var(--light-color); padding: 12px; border-radius: 8px;">
                   ${player.speeches.map(speech => `
                       <div style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--border-color);">
                           <small style="color: #7f8c8d;">${speech.phase}</small>
                           <p>${speech.content}</p>
                       </div>
                   `).join('')}
               </div>`
            : '<p style="color: #7f8c8d;">暂无发言记录</p>';

        modalBody.innerHTML = `
            <div style="margin-bottom: 16px;">
                <strong>角色：</strong>
                <span style="color: var(--primary-color); font-weight: 700;">
                    ${this.showRoles || player.is_revealed ? player.role : '???'}
                </span>
            </div>
            <div style="margin-bottom: 16px;">
                <strong>状态：</strong>
                <span class="status-badge ${player.status === '存活' ? 'alive' : 'dead'}">${player.status}</span>
            </div>
            ${actionsHtml}
            ${speechesHtml}
        `;

        modal.classList.add('active');
    }

    closeModal() {
        const modal = document.getElementById('playerModal');
        modal.classList.remove('active');
    }
}

// 初始化游戏
document.addEventListener('DOMContentLoaded', () => {
    const game = new WerewolfGame();
});
