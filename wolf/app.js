const PHASE_NAME = {
  idle: "未开始",
  init: "初始化",
  night: "夜间",
  dawn: "天亮",
  speech: "发言",
  vote: "投票",
  gameover: "游戏结束",
};

const ROLE_META = {
  wolf: { label: "狼人", groupClass: "wolf" },
  villager: { label: "村民", groupClass: "villager" },
  seer: { label: "预言家", groupClass: "god" },
  witch: { label: "女巫", groupClass: "god" },
  hunter: { label: "猎人", groupClass: "god" },
  guard: { label: "守卫", groupClass: "god" },
};

const dom = {
  playerCount: document.getElementById("player-count"),
  speedControl: document.getElementById("speed-control"),
  roleToggleBtn: document.getElementById("role-toggle-btn"),
  revealPolicy: document.getElementById("reveal-policy"),
  startBtn: document.getElementById("start-btn"),
  pauseBtn: document.getElementById("pause-btn"),
  resumeBtn: document.getElementById("resume-btn"),
  resetBtn: document.getElementById("reset-btn"),
  currentPhase: document.getElementById("current-phase"),
  currentRound: document.getElementById("current-round"),
  gameStatus: document.getElementById("game-status"),
  aliveCount: document.getElementById("alive-count"),
  playerList: document.getElementById("player-list"),
  actionStage: document.getElementById("action-stage"),
  timeline: document.getElementById("timeline"),
  timelineHint: document.getElementById("timeline-hint"),
  selectedAi: document.getElementById("selected-ai"),
  thoughtProgress: document.getElementById("thought-progress"),
  thoughtLive: document.getElementById("thought-live"),
  thoughtHistory: document.getElementById("thought-history"),
  thoughtLock: document.getElementById("thought-lock"),
  thoughtLatest: document.getElementById("thought-latest"),
  thoughtNewHint: document.getElementById("thought-new-hint"),
  thoughtPause: document.getElementById("thought-pause"),
  thoughtReplay: document.getElementById("thought-replay"),
  thoughtCopy: document.getElementById("thought-copy"),
  fullRecord: document.getElementById("full-record"),
  clearLog: document.getElementById("clear-log"),
  llmProvider: document.getElementById("llm-provider"),
  llmModel: document.getElementById("llm-model"),
  llmTemperature: document.getElementById("llm-temperature"),
  llmBaseUrl: document.getElementById("llm-base-url"),
  llmApiKey: document.getElementById("llm-api-key"),
  saveConfig: document.getElementById("save-config"),
  llmCheckMsg: document.getElementById("llm-check-msg"),
  summaryHint: document.getElementById("summary-hint"),
  restoreBanner: document.getElementById("restore-banner"),
};

const view = {
  state: null,
  selectedPlayerId: null,
  selectedThoughtId: null,
  thoughtPaused: false,
  typingTimer: null,
  eventSource: null,
  reconnectTimer: null,
  configMsgTimer: null,
  llmConfigDirty: false,
  thoughtLocked: true,
  thoughtPendingCount: 0,
};

init();

async function init() {
  populatePlayerCount();
  bindEvents();
  if (dom.restoreBanner) dom.restoreBanner.classList.add("hidden");
  await refreshState();
  startEventStream();
}

function populatePlayerCount() {
  for (let i = 6; i <= 12; i += 1) {
    const opt = document.createElement("option");
    opt.value = String(i);
    opt.textContent = `${i} 人`;
    if (i === 12) opt.selected = true;
    dom.playerCount.appendChild(opt);
  }
}

function bindEvents() {
  dom.startBtn.addEventListener("click", async () => {
    await apiPost("/api/game/start", collectGameConfig());
    await refreshState();
  });

  dom.pauseBtn.addEventListener("click", async () => {
    await apiPost("/api/game/pause");
    await refreshState();
  });

  dom.resumeBtn.addEventListener("click", async () => {
    await apiPost("/api/game/resume");
    await refreshState();
  });

  dom.resetBtn.addEventListener("click", async () => {
    await apiPost("/api/game/reset");
    clearTyping();
    await refreshState();
  });

  dom.speedControl.addEventListener("change", saveGameConfig);
  dom.revealPolicy.addEventListener("change", saveGameConfig);
  dom.playerCount.addEventListener("change", saveGameConfig);
  dom.roleToggleBtn.addEventListener("click", async () => {
    const current = !!view.state?.settings?.reveal_roles;
    if (!view.state?.settings) return;
    view.state.settings.reveal_roles = !current;
    renderPlayers();
    renderRoleToggleButton();
    await saveGameConfig();
  });

  dom.clearLog.addEventListener("click", () => {
    dom.timeline.innerHTML = "";
  });

  dom.thoughtPause.addEventListener("click", () => {
    view.thoughtPaused = !view.thoughtPaused;
    dom.thoughtPause.textContent = view.thoughtPaused ? "继续打字" : "暂停打字";
  });

  dom.thoughtReplay.addEventListener("click", () => {
    const thought = getSelectedThought();
    if (!thought) return;
    playTypingThought(thought.text, thought.source, true);
  });

  dom.thoughtCopy.addEventListener("click", async () => {
    const thought = getSelectedThought();
    if (!thought) return;
    try {
      await navigator.clipboard.writeText(thought.text);
    } catch (_) {}
  });

  dom.thoughtLock.addEventListener("click", () => {
    view.thoughtLocked = !view.thoughtLocked;
    if (!view.thoughtLocked) {
      jumpToLatestThought(true);
    }
    renderThoughtLockUi();
  });

  dom.thoughtLatest.addEventListener("click", () => {
    jumpToLatestThought(true);
  });

  dom.saveConfig.addEventListener("click", async () => {
    const result = await apiPost("/api/config/llm", {
      provider: dom.llmProvider.value,
      model: dom.llmModel.value.trim(),
      temperature: Number(dom.llmTemperature.value),
      base_url: dom.llmBaseUrl.value.trim(),
      api_key: dom.llmApiKey.value.trim(),
    });
    if (!result) {
      notifyConfigCheck("保存失败：无法连接后端", true);
      return;
    }
    if (result.ok) {
      view.llmConfigDirty = false;
    }
    await refreshState();
    notifyConfigCheck(result.message || (result.ok ? "配置保存成功" : "配置校验失败"), !result.ok);
  });

  dom.llmProvider.addEventListener("change", () => {
    view.llmConfigDirty = true;
    const provider = dom.llmProvider.value;
    if (provider === "glm" && (!dom.llmBaseUrl.value || dom.llmBaseUrl.value.includes("api.openai.com"))) {
      dom.llmBaseUrl.value = "https://open.bigmodel.cn/api/paas/v4";
    }
    if (provider === "openai" && dom.llmBaseUrl.value.includes("open.bigmodel.cn")) {
      dom.llmBaseUrl.value = "https://api.openai.com/v1";
    }
  });

  [dom.llmModel, dom.llmTemperature, dom.llmBaseUrl, dom.llmApiKey].forEach((el) => {
    el.addEventListener("input", () => {
      view.llmConfigDirty = true;
    });
  });
}

function collectGameConfig() {
  return {
    player_count: Number(dom.playerCount.value),
    speed: dom.speedControl.value,
    reveal_roles: !!view.state?.settings?.reveal_roles,
    reveal_policy: dom.revealPolicy.value,
  };
}

async function saveGameConfig() {
  await apiPost("/api/config/game", collectGameConfig());
}

async function refreshState() {
  const next = await apiGet("/api/state");
  if (!next) return;
  applyState(next);
}

function applyState(next) {
  const prevState = view.state;
  const prevThoughtId = view.selectedThoughtId;
  view.state = next;
  const live = next.llm_live;
  const hasLive = !!(live && live.active);
  const newThoughts = countNewThoughts(prevState, next);

  if (!view.selectedPlayerId && next.players?.length) {
    view.selectedPlayerId = next.players[0].id;
  }

  if (view.thoughtLocked) {
    if (newThoughts > 0) {
      view.thoughtPendingCount += newThoughts;
    }
    const selectedPlayer = getSelectedPlayer();
    if (!selectedPlayer || selectedPlayer.history.length === 0) {
      view.selectedThoughtId = null;
      dom.thoughtLive.textContent = "";
    } else if (!selectedPlayer.history.find((h) => h.id === view.selectedThoughtId)) {
      view.selectedThoughtId = selectedPlayer.history[selectedPlayer.history.length - 1].id;
    }
  } else if (!hasLive) {
    const selectedPlayer = getSelectedPlayer();
    if (selectedPlayer && selectedPlayer.history.length > 0) {
      const latest = selectedPlayer.history[selectedPlayer.history.length - 1];
      if (!prevThoughtId || !selectedPlayer.history.find((h) => h.id === prevThoughtId)) {
        view.selectedThoughtId = latest.id;
        playTypingThought(latest.text, latest.source, true);
      } else {
        const current = selectedPlayer.history.find((h) => h.id === prevThoughtId);
        if (current && dom.thoughtLive.textContent.length === 0) {
          playTypingThought(current.text, current.source, true);
        }
      }
    } else {
      view.selectedThoughtId = null;
      dom.thoughtLive.textContent = "";
    }
    view.thoughtPendingCount = 0;
  }

  syncControlsFromState(next);
  render();
  renderThoughtLockUi();
}

function renderLiveThought() {
  const live = view.state?.llm_live;
  if (!live || !live.active) return;
  if (live.player_id && view.selectedPlayerId !== live.player_id) return;
  clearTyping();
  const header = `【思考来源：${live.source || "模型"}】\n`;
  const text = live.text && live.text.trim() ? live.text : "正在思考中...";
  dom.thoughtLive.textContent = `${header}${text}`;
}

function startEventStream() {
  if (view.eventSource) {
    view.eventSource.close();
    view.eventSource = null;
  }
  if (view.reconnectTimer) {
    clearTimeout(view.reconnectTimer);
    view.reconnectTimer = null;
  }

  const last = Number.isFinite(view.state?.revision) ? view.state.revision : -1;
  const es = new EventSource(`/api/events?last=${last}`);
  view.eventSource = es;

  es.addEventListener("state", (event) => {
    try {
      const payload = JSON.parse(event.data);
      applyState(payload);
    } catch (_) {}
  });

  es.onerror = () => {
    dom.timelineHint.textContent = "实时连接中断，正在重连...";
    if (view.eventSource) {
      view.eventSource.close();
      view.eventSource = null;
    }
    if (view.reconnectTimer) clearTimeout(view.reconnectTimer);
    view.reconnectTimer = setTimeout(() => {
      startEventStream();
    }, 1500);
  };
}

function syncControlsFromState(state) {
  const s = state.settings || {};
  if (s.player_count) dom.playerCount.value = String(s.player_count);
  if (s.speed) dom.speedControl.value = s.speed;
  if (s.reveal_policy) dom.revealPolicy.value = s.reveal_policy;
  renderRoleToggleButton();

  if (!view.llmConfigDirty) {
    const llm = state.llm_config || {};
    if (llm.provider) dom.llmProvider.value = llm.provider;
    if (llm.model) dom.llmModel.value = llm.model;
    if (Number.isFinite(llm.temperature)) dom.llmTemperature.value = String(llm.temperature);
    if (llm.base_url) dom.llmBaseUrl.value = llm.base_url;
  }
}

function render() {
  renderMeta();
  renderRoleToggleButton();
  renderThoughtLockUi();
  renderPlayers();
  renderTimeline();
  renderStage();
  renderThoughtPanel();
  renderRecords();
}

function renderMeta() {
  if (!view.state) return;
  dom.currentPhase.textContent = view.state.phase_label || PHASE_NAME[view.state.phase] || "-";
  dom.currentRound.textContent = String(view.state.round || 0);
  dom.gameStatus.textContent =
    view.state.status === "running" ? "运行中" : view.state.status === "paused" ? "已暂停" : view.state.status === "ended" ? "已结束" : "待机";
  const alive = (view.state.players || []).filter((p) => p.alive).length;
  dom.aliveCount.textContent = `${alive} 存活`;
  dom.timelineHint.textContent = view.state.winner ? `${view.state.winner}阵营胜利` : "实时刷新中";
  dom.summaryHint.textContent = view.state.winner ? `胜利阵营：${view.state.winner}` : "游戏结束后可查看完整回放";
}

function renderPlayers() {
  dom.playerList.innerHTML = "";
  const players = view.state?.players || [];

  for (const p of players) {
    const card = document.createElement("div");
    card.className = `player-card ${p.id === view.selectedPlayerId ? "active" : ""}`;

    const top = document.createElement("div");
    top.className = "player-top";
    const left = document.createElement("div");
    left.style.display = "flex";
    left.style.gap = "8px";
    left.style.alignItems = "center";

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = p.avatar;

    const nameWrap = document.createElement("div");
    nameWrap.innerHTML = `<strong>${escapeHtml(p.name)}</strong><div style="font-size:12px;color:#63686d">${escapeHtml(p.id)}</div>`;

    left.appendChild(avatar);
    left.appendChild(nameWrap);

    const stateTag = document.createElement("span");
    stateTag.className = `state ${p.alive ? "alive" : "dead"}`;
    stateTag.textContent = p.alive ? "存活" : "死亡";

    top.appendChild(left);
    top.appendChild(stateTag);
    card.appendChild(top);

    const showRole = shouldShowRole(p);
    const role = document.createElement("div");
    role.className = `role-pill ${showRole ? ROLE_META[p.role]?.groupClass || "villager" : "villager"}`;
    role.textContent = showRole ? ROLE_META[p.role]?.label || p.role : "身份隐藏";
    card.appendChild(role);

    card.addEventListener("click", () => {
      view.selectedPlayerId = p.id;
      view.selectedThoughtId = p.history[p.history.length - 1]?.id || null;
      view.thoughtPendingCount = 0;
      renderPlayers();
      renderThoughtPanel();
      renderThoughtLockUi();
      const t = getSelectedThought();
      if (t) playTypingThought(t.text, t.source, true);
    });

    dom.playerList.appendChild(card);
  }
}

function renderTimeline() {
  dom.timeline.innerHTML = "";
  const logs = view.state?.logs || [];
  for (const item of logs.slice(-220).reverse()) {
    const el = document.createElement("div");
    el.className = "log-item";
    el.innerHTML = `
      <div class="log-meta">R${item.round} · ${PHASE_NAME[item.phase] || item.phase} · ${item.ts}</div>
      <div><strong>${escapeHtml(item.actor)}</strong>：${escapeHtml(item.text)}</div>
    `;
    dom.timeline.appendChild(el);
  }
}

function renderStage() {
  dom.actionStage.innerHTML = "";
  const stage = view.state?.stage_lines || [];
  if (!stage.length) {
    dom.actionStage.innerHTML = "<div class='stage-line'>等待开始</div>";
    return;
  }
  for (const line of stage.slice().reverse()) {
    const div = document.createElement("div");
    div.className = "stage-line";
    div.textContent = line;
    dom.actionStage.appendChild(div);
  }
}

function renderThoughtPanel() {
  const player = getSelectedPlayer();
  dom.selectedAi.textContent = `当前：${player ? player.name : "无"}`;
  dom.thoughtHistory.innerHTML = "";

  if (!player) {
    dom.thoughtProgress.textContent = "-";
    dom.thoughtLive.textContent = "";
    return;
  }

  const history = player.history || [];
  dom.thoughtProgress.textContent = `${history.length} 条记录`;
  for (const item of history.slice().reverse()) {
    const el = document.createElement("div");
    el.className = `thought-item ${item.id === view.selectedThoughtId ? "active" : ""}`;
    const sourceText = item.source || "虚拟";
    el.innerHTML = `<div style="font-size:12px;color:#63686d">R${item.round} · ${escapeHtml(item.action)} · ${item.ts} · 来源:${escapeHtml(sourceText)}</div><div>${escapeHtml(item.text.slice(0, 45))}...</div>`;
    el.addEventListener("click", () => {
      view.selectedThoughtId = item.id;
      view.thoughtPendingCount = 0;
      renderThoughtPanel();
      renderThoughtLockUi();
      playTypingThought(item.text, item.source, true);
    });
    dom.thoughtHistory.appendChild(el);
  }
}

function renderThoughtLockUi() {
  if (!dom.thoughtLock || !dom.thoughtLatest || !dom.thoughtNewHint) return;
  dom.thoughtLock.textContent = view.thoughtLocked ? "锁定查看" : "跟随最新";
  dom.thoughtLatest.disabled = !view.state || !view.state.players || view.state.players.length === 0;
  if (view.thoughtPendingCount > 0) {
    dom.thoughtNewHint.classList.remove("hidden");
    dom.thoughtNewHint.textContent = `有新记录 +${view.thoughtPendingCount}`;
  } else {
    dom.thoughtNewHint.classList.add("hidden");
  }
}

function jumpToLatestThought(play = false) {
  const player = getSelectedPlayer();
  if (!player || !player.history || player.history.length === 0) return;
  const latest = player.history[player.history.length - 1];
  view.selectedThoughtId = latest.id;
  view.thoughtPendingCount = 0;
  renderThoughtPanel();
  renderThoughtLockUi();
  if (play) playTypingThought(latest.text, latest.source, true);
}

function countNewThoughts(prevState, nextState) {
  if (!prevState || !prevState.players || !nextState || !nextState.players) return 0;
  const prevMap = new Map(prevState.players.map((p) => [p.id, (p.history || []).length]));
  let delta = 0;
  for (const p of nextState.players) {
    const prevLen = prevMap.get(p.id) || 0;
    const curLen = (p.history || []).length;
    if (curLen > prevLen) delta += curLen - prevLen;
  }
  return delta;
}

function renderRecords() {
  const records = view.state?.records || [];
  dom.fullRecord.textContent = records
    .map((r) => `[R${r.round}][${r.phase}][${r.ts}] ${r.actor}: ${r.note}`)
    .join("\n");
}

function getSelectedPlayer() {
  const players = view.state?.players || [];
  return players.find((p) => p.id === view.selectedPlayerId) || null;
}

function getSelectedThought() {
  const player = getSelectedPlayer();
  if (!player) return null;
  return player.history.find((h) => h.id === view.selectedThoughtId) || player.history[player.history.length - 1] || null;
}

function shouldShowRole(player) {
  const st = view.state;
  if (!st) return false;
  if (st.settings?.reveal_roles) return true;
  if (st.status === "ended") return true;
  if (!player.alive && st.settings?.reveal_policy === "onDeath") return true;
  if (player.revealed) return true;
  return false;
}

function renderRoleToggleButton() {
  if (!dom.roleToggleBtn) return;
  const show = !!view.state?.settings?.reveal_roles;
  dom.roleToggleBtn.textContent = show ? "隐藏身份" : "显示身份";
}

function playTypingThought(text, source = "虚拟", force = false) {
  if (!text) return;
  if (force) clearTyping();
  const speed = view.state?.settings?.speed || "normal";
  const stepMs = speed === "fast" ? 10 : speed === "slow" ? 32 : 18;

  const header = `【思考来源：${source || "虚拟"}】\n`;
  const displayText = `${header}${text}`;
  let i = 0;
  dom.thoughtLive.textContent = "";
  view.typingTimer = setInterval(() => {
    if (view.thoughtPaused) return;
    i += 1;
    dom.thoughtLive.textContent = displayText.slice(0, i);
    if (i >= displayText.length) clearTyping();
  }, stepMs);
}

function clearTyping() {
  if (view.typingTimer) {
    clearInterval(view.typingTimer);
    view.typingTimer = null;
  }
}

async function apiGet(url) {
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    return await res.json();
  } catch (_) {
    return null;
  }
}

async function apiPost(url, body = null) {
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : "{}",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (_) {
    return null;
  }
}

function notifyConfigCheck(message, isError = false) {
  dom.timelineHint.textContent = message;
  if (!dom.llmCheckMsg) return;
  dom.llmCheckMsg.textContent = message;
  dom.llmCheckMsg.classList.remove("hidden", "error");
  if (isError) dom.llmCheckMsg.classList.add("error");
  if (view.configMsgTimer) clearTimeout(view.configMsgTimer);
  view.configMsgTimer = setTimeout(() => {
    dom.llmCheckMsg.classList.add("hidden");
  }, isError ? 8000 : 5000);
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
