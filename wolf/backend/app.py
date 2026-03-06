import json
import logging
import os
import random
import threading
import time
import re
from difflib import SequenceMatcher
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from flask import Flask, Response, jsonify, request, send_from_directory

LOG_LEVEL = os.getenv("WOLF_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("wolf")


ROLE_META = {
    "wolf": {"label": "狼人", "team": "wolf", "group": "wolf"},
    "villager": {"label": "村民", "team": "villager", "group": "villager"},
    "seer": {"label": "预言家", "team": "god", "group": "god"},
    "witch": {"label": "女巫", "team": "god", "group": "god"},
    "hunter": {"label": "猎人", "team": "god", "group": "god"},
    "guard": {"label": "守卫", "team": "god", "group": "god"},
}

ROLE_POOL = {
    6: ["wolf", "wolf", "villager", "villager", "seer", "witch"],
    7: ["wolf", "wolf", "villager", "villager", "seer", "witch", "hunter"],
    8: ["wolf", "wolf", "villager", "villager", "villager", "seer", "witch", "hunter"],
    9: ["wolf", "wolf", "wolf", "villager", "villager", "villager", "seer", "witch", "hunter"],
    10: ["wolf", "wolf", "wolf", "villager", "villager", "villager", "villager", "seer", "witch", "hunter"],
    11: ["wolf", "wolf", "wolf", "villager", "villager", "villager", "villager", "seer", "witch", "hunter", "guard"],
    12: ["wolf", "wolf", "wolf", "wolf", "villager", "villager", "villager", "villager", "seer", "witch", "hunter", "guard"],
}

PLAYER_NAMES = [
    "青岚", "北斗", "赤羽", "东篱", "繁星", "观棋", "海灯", "见山", "临风", "明川", "南柯", "听雪", "忘机", "言午", "知白", "子衿", "朝露", "惊鸿",
]

PHASE_NAME = {
    "idle": "未开始",
    "init": "初始化",
    "night": "夜间",
    "dawn": "天亮",
    "speech": "发言",
    "vote": "投票",
    "gameover": "游戏结束",
}

SPEED_SEC = {"slow": 1.0, "normal": 0.56, "fast": 0.26}


class GameEngine:
    def __init__(self):
        self.lock = threading.RLock()
        self.update_cond = threading.Condition(self.lock)
        self.state_revision = 0
        self.run_token = 0
        self.worker = None
        self.config_file = Path(__file__).resolve().parent / "llm_config.json"
        self.llm_config = {
            "provider": "mock",
            "model": "gpt-4.1-mini",
            "temperature": 0.7,
            "base_url": "https://api.openai.com/v1",
            "api_key": "",
        }
        self._load_llm_config_from_disk()
        self.state = self._initial_state()

    def _initial_state(self):
        return {
            "players": [],
            "round": 0,
            "phase": "idle",
            "status": "idle",
            "winner": None,
            "settings": {
                "player_count": 12,
                "speed": "normal",
                "reveal_roles": False,
                "reveal_policy": "endOnly",
            },
            "logs": [],
            "stage_lines": [],
            "records": [],
            "elimination_order": [],
            "vote_stats": {},
            "public_claims": [],
            "llm_live": None,
            "llm_metrics": {
                "requests": 0,
                "success": 0,
                "failed": 0,
                "last_status": "",
                "last_error": "",
                "last_at": "",
            },
        }

    def snapshot(self):
        with self.lock:
            return self._snapshot_locked()

    def _snapshot_locked(self):
        data = deepcopy(self.state)
        data["phase_label"] = PHASE_NAME.get(data["phase"], data["phase"])
        data["llm_config"] = {**self.llm_config, "api_key": "" if not self.llm_config.get("api_key") else "******"}
        data["revision"] = self.state_revision
        return data

    def _mark_updated_locked(self):
        with self.lock:
            self.state_revision += 1
            self.update_cond.notify_all()

    def wait_for_update(self, last_revision, timeout=25):
        with self.lock:
            changed = self.update_cond.wait_for(lambda: self.state_revision != last_revision, timeout=timeout)
            if not changed:
                return None
            return self._snapshot_locked()

    def configure_llm(self, payload):
        with self.lock:
            self.llm_config["provider"] = payload.get("provider", "mock")
            self.llm_config["model"] = payload.get("model", "gpt-4.1-mini")
            self.llm_config["temperature"] = max(0, min(2, float(payload.get("temperature", 0.7))))
            self.llm_config["base_url"] = payload.get("base_url", "https://api.openai.com/v1")
            self.llm_config["api_key"] = payload.get("api_key", "")
            self._save_llm_config_to_disk()
            self._mark_updated_locked()
            logger.info(
                "llm configured provider=%s model=%s base_url=%s",
                self.llm_config["provider"],
                self.llm_config["model"],
                self.llm_config["base_url"],
            )

    def validate_llm_config(self):
        cfg = deepcopy(self.llm_config)
        provider = cfg.get("provider", "mock")
        if provider == "mock":
            return True, "Mock 模式可用（来源将显示为“虚拟”）"
        if provider not in {"openai", "glm"}:
            return False, f"不支持的提供方：{provider}"

        if not cfg.get("api_key"):
            return False, "缺少 API Key"
        if not cfg.get("base_url"):
            return False, "缺少 API Base URL"
        if not cfg.get("model"):
            return False, "缺少模型名称"

        base = cfg["base_url"].rstrip("/")
        try:
            resp = self._post_chat_completions(
                base_url=base,
                api_key=cfg["api_key"],
                payload={
                    "model": cfg["model"],
                    "temperature": 0,
                    "messages": [{"role": "user", "content": "reply ok"}],
                    "max_tokens": 16,
                },
                timeout=6,
            )
            if not resp.ok:
                text = (resp.text or "").strip().replace("\n", " ")
                text = text[:120] if text else "unknown error"
                return False, f"模型校验失败（HTTP {resp.status_code}）：{text}"
            data = resp.json()
            content = self._extract_text_from_chat_response(data)
            if content:
                provider_name = "GLM" if provider == "glm" else "OpenAI兼容"
                return True, f"{provider_name} 模型可用：{cfg['model']}"
            finish_reason = data.get("choices", [{}])[0].get("finish_reason", "unknown")
            usage = data.get("usage", {})
            if finish_reason in {"stop", "length"} or usage:
                provider_name = "GLM" if provider == "glm" else "OpenAI兼容"
                return True, f"{provider_name} 接口连通：{cfg['model']}（finish_reason={finish_reason}）"
            return False, f"模型校验失败：返回内容为空（finish_reason={finish_reason}）"
        except Exception as exc:
            return False, f"模型校验失败：{exc}"

    def configure_game(self, payload):
        with self.lock:
            count = int(payload.get("player_count", self.state["settings"]["player_count"]))
            if count < 6 or count > 12:
                return False, "人数必须在6-12之间"

            # During running game, allow UI/display settings updates,
            # but do not allow changing player count.
            if self.state["status"] == "running" and count != self.state["settings"]["player_count"]:
                return False, "游戏运行中，不能修改人数"

            self.state["settings"]["player_count"] = count
            self.state["settings"]["speed"] = payload.get("speed", self.state["settings"]["speed"])
            self.state["settings"]["reveal_roles"] = bool(payload.get("reveal_roles", self.state["settings"]["reveal_roles"]))
            self.state["settings"]["reveal_policy"] = payload.get("reveal_policy", self.state["settings"]["reveal_policy"])
            self._mark_updated_locked()
            logger.info(
                "game configured players=%s speed=%s reveal_roles=%s reveal_policy=%s",
                self.state["settings"]["player_count"],
                self.state["settings"]["speed"],
                self.state["settings"]["reveal_roles"],
                self.state["settings"]["reveal_policy"],
            )
            return True, "ok"

    def start(self):
        with self.lock:
            if self.state["status"] == "running":
                logger.info("start ignored: already running")
                return
            if self.state["status"] == "paused" and self.state["players"] and not self.state["winner"]:
                self.state["status"] = "running"
                self._log("系统", "游戏继续")
                self._spawn_worker_locked()
                logger.info("game resumed from paused state")
                return
            self.run_token += 1
            token = self.run_token
            kept_settings = deepcopy(self.state.get("settings", {}))
            self.state = self._initial_state()
            self.state["settings"].update(kept_settings)
            self.state["status"] = "running"
            self.state["phase"] = "init"
            self._setup_players(self.state["settings"]["player_count"])
            self._log("系统", f"开局：{self.state['settings']['player_count']}人局，角色已分配")
            self._record("系统", "初始化", "角色分配完成")
            self._stage("游戏初始化完成，进入夜晚")
            self._spawn_worker_locked(token)
            logger.info("game started token=%s players=%s", token, self.state["settings"]["player_count"])

    def pause(self):
        with self.lock:
            if self.state["status"] == "running":
                self.state["status"] = "paused"
                self._log("系统", "游戏已暂停")
                logger.info("game paused round=%s phase=%s", self.state["round"], self.state["phase"])

    def resume(self):
        with self.lock:
            if self.state["status"] == "paused":
                self.state["status"] = "running"
                self._log("系统", "游戏继续")
                self._spawn_worker_locked()
                logger.info("game resumed round=%s phase=%s", self.state["round"], self.state["phase"])

    def reset(self):
        with self.lock:
            self.run_token += 1
            self.state = self._initial_state()
            self._mark_updated_locked()
            logger.info("game reset")

    def _spawn_worker_locked(self, token=None):
        if token is None:
            token = self.run_token
        if self.worker and self.worker.is_alive():
            return
        self.worker = threading.Thread(target=self._run_loop, args=(token,), daemon=True)
        self.worker.start()

    def _setup_players(self, count):
        roles = ROLE_POOL[count][:]
        random.shuffle(roles)
        names = PLAYER_NAMES[:]
        random.shuffle(names)

        players = []
        for idx, role in enumerate(roles):
            players.append(
                {
                    "id": f"p{idx + 1}",
                    "name": names[idx],
                    "avatar": names[idx][0],
                    "role": role,
                    "team": ROLE_META[role]["team"],
                    "alive": True,
                    "revealed": False,
                    "history": [],
                    "speeches": [],
                    "memory": {"seer_checks": [], "known_wolves": [], "claimed_seer": False},
                    "abilities": {
                        "antidote": role == "witch",
                        "poison": role == "witch",
                        "shot_used": False if role == "hunter" else True,
                        "last_guard": None,
                    },
                }
            )
        self.state["players"] = players

    def _run_loop(self, token):
        try:
            while True:
                if not self._valid_to_run(token):
                    return
                self._wait_if_paused(token)
                if not self._valid_to_run(token):
                    return

                with self.lock:
                    self.state["round"] += 1
                    rd = self.state["round"]
                    self.state["phase"] = "night"
                    self._stage(f"第 {rd} 夜：进入夜间行动")
                    logger.info("round start round=%s", rd)

                self._run_night(token)
                if self._maybe_end_game(token):
                    return

                with self.lock:
                    self.state["phase"] = "dawn"
                    self._stage(f"第 {self.state['round']} 天：公布夜间结果")
                self._run_dawn(token)
                if self._maybe_end_game(token):
                    return

                with self.lock:
                    self.state["phase"] = "speech"
                    self._stage(f"第 {self.state['round']} 天：发言阶段")
                speech_count = self._run_speech(token)
                if self._maybe_end_game(token):
                    return

                if speech_count <= 0:
                    self._host_say("本轮发言阶段未形成有效发言，按规则本轮跳过投票，进入下一夜。", "发言")
                    continue

                with self.lock:
                    self.state["phase"] = "vote"
                    self._stage(f"第 {self.state['round']} 天：投票阶段")
                self._run_vote(token)
                if self._maybe_end_game(token):
                    return
        except Exception as exc:
            with self.lock:
                self._log("系统", f"流程异常中断：{type(exc).__name__}:{str(exc)[:180]}")
                self.state["status"] = "paused"
                self._mark_updated_locked()
                logger.exception("run loop failed token=%s", token)

    def _run_night(self, token):
        with self.lock:
            alive = self._alive_players()
            wolves = [p for p in alive if p["role"] == "wolf"]
            seer = self._find_alive_role("seer")
            witch = self._find_alive_role("witch")
            guard = self._find_alive_role("guard")

        self._host_say("夜幕降临，所有玩家请闭眼。", "夜间")
        wolf_target = None
        self._host_say("进入狼人环节。狼人请睁眼，选择今夜袭击目标。", "夜间")
        if wolves:
            lead = None
            target_name = None
            wolf_votes = {}
            with self.lock:
                targets = [p for p in self._alive_players() if p["role"] != "wolf"]
                if targets and wolves:
                    lead = wolves[0]
                    # Each alive wolf scores and votes; pack picks majority target.
                    for wolf in wolves:
                        ranked = sorted(targets, key=lambda t: self._suspicion_score(t, wolf), reverse=True)
                        if ranked:
                            pick = ranked[0]
                            wolf_votes[pick["id"]] = wolf_votes.get(pick["id"], 0) + 1
                    if wolf_votes:
                        max_vote = max(wolf_votes.values())
                        top_ids = [pid for pid, c in wolf_votes.items() if c == max_vote]
                        wolf_target = random.choice(top_ids)
                        target_name = self._name_of(wolf_target)
            if wolf_target and lead and target_name:
                vote_view = "，".join([f"{self._name_of(pid)}:{cnt}" for pid, cnt in wolf_votes.items()])
                self._emit_thought(lead, "夜间袭击", f"狼队集体讨论后锁定 {target_name}（票型：{vote_view}）。")
                with self.lock:
                    self._log("狼人", f"集体票型：{vote_view}", public=False)
                    self._log("狼人", f"锁定袭击目标：{target_name}", public=False)
                    self._record("狼人", "夜间", f"集体决策袭击：{target_name}（{vote_view}）", public=False)
        else:
            self._host_say("狼人已全部出局，狼人环节跳过。", "夜间")
        self._host_say("狼人行动结束，狼人请闭眼。", "夜间")
        self._sleep_step(token, 1)

        self._host_say("进入预言家环节。预言家请睁眼，选择查验目标。", "夜间")
        if seer:
            seer_target_name = None
            seer_is_wolf = None
            with self.lock:
                target = self._choose_seer_target(seer)
                if target:
                    is_wolf = target["role"] == "wolf"
                    seer["memory"]["seer_checks"].append({"round": self.state["round"], "target_id": target["id"], "is_wolf": is_wolf})
                    if is_wolf and target["id"] not in seer["memory"]["known_wolves"]:
                        seer["memory"]["known_wolves"].append(target["id"])
                    seer_target_name = target["name"]
                    seer_is_wolf = is_wolf
            if seer_target_name is not None:
                self._emit_thought(seer, "夜间查验", f"查验 {seer_target_name}，结果为{'狼人' if seer_is_wolf else '好人'}。")
                with self.lock:
                    self._log(seer["name"], f"查验了 {seer_target_name}", public=False)
                    self._record(seer["name"], "夜间", f"查验：{seer_target_name} => {'狼人' if seer_is_wolf else '好人'}", public=False)
        else:
            self._host_say("预言家已出局，预言家环节跳过。", "夜间")
        self._host_say("预言家行动结束，预言家请闭眼。", "夜间")
        self._sleep_step(token, 0.9)

        saved = False
        poison_target = None
        self._host_say("进入女巫环节。女巫请睁眼，请决定是否使用解药或毒药。", "夜间")
        if witch:
            witch_emit_line = None
            witch_log_line = None
            witch_record_line = None
            witch_extra_context = ""
            with self.lock:
                action = self._choose_witch_action(witch, wolf_target)
                if action["type"] == "save" and wolf_target:
                    wt = self._player_by_id(wolf_target)
                    self._host_say(f"（仅女巫可见）今晚被袭击的是 {wt['name']}，请决定是否使用解药。", "夜间", public=False)
                    witch_extra_context = f"主持人私密告知：今夜刀口是{wt['name']}"
                    saved = True
                    witch["abilities"]["antidote"] = False
                    witch_emit_line = f"主持人提示今晚被刀的是 {wt['name']}，我判断值得救下。"
                    witch_log_line = f"使用了解药，救下 {wt['name']}"
                    witch_record_line = f"解药：{wt['name']}"
                elif action["type"] == "poison" and action["target_id"]:
                    if wolf_target:
                        wt = self._player_by_id(wolf_target)
                        if wt:
                            self._host_say(f"（仅女巫可见）今晚被袭击的是 {wt['name']}，请决定是否用药。", "夜间", public=False)
                            witch_extra_context = f"主持人私密告知：今夜刀口是{wt['name']}"
                    pt = self._player_by_id(action["target_id"])
                    poison_target = pt["id"]
                    witch["abilities"]["poison"] = False
                    witch_emit_line = f"毒杀 {pt['name']}，压缩狼人生存空间。"
                    witch_log_line = f"使用毒药，目标 {pt['name']}"
                    witch_record_line = f"毒药：{pt['name']}"
                else:
                    if wolf_target:
                        wt = self._player_by_id(wolf_target)
                        if wt:
                            self._host_say(f"（仅女巫可见）今晚被袭击的是 {wt['name']}，你选择不使用解药。", "夜间", public=False)
                            witch_extra_context = f"主持人私密告知：今夜刀口是{wt['name']}"
                    witch_emit_line = "本轮选择观望，保留药权。"
                    witch_log_line = "未使用药剂"
                    witch_record_line = "未使用药剂"
            if witch_emit_line:
                self._emit_thought(witch, "夜间用药", witch_emit_line, extra_context=witch_extra_context)
                with self.lock:
                    self._log(witch["name"], witch_log_line, public=False)
                    self._record(witch["name"], "夜间", witch_record_line, public=False)
        else:
            self._host_say("女巫已出局，女巫环节跳过。", "夜间")
        self._host_say("女巫行动结束，女巫请闭眼。", "夜间")
        self._sleep_step(token, 0.8)

        guard_target = None
        self._host_say("进入守卫环节。守卫请睁眼，选择守护目标。", "夜间")
        if guard:
            guard_name = None
            pick_name = None
            with self.lock:
                candidates = [p for p in self._alive_players() if p["id"] != guard["abilities"]["last_guard"]]
                if candidates:
                    pick = random.choice(candidates)
                    guard_target = pick["id"]
                    guard["abilities"]["last_guard"] = guard_target
                    guard_name = guard["name"]
                    pick_name = pick["name"]
            if guard_target and pick_name:
                self._emit_thought(guard, "夜间守护", f"{pick_name}可能是关键位，优先守护。")
                with self.lock:
                    self._log(guard_name, f"守护了 {pick_name}", public=False)
                    self._record(guard_name, "夜间", f"守护目标：{pick_name}", public=False)
        else:
            self._host_say("守卫已出局或本局无守卫，守卫环节跳过。", "夜间")
        self._host_say("守卫行动结束，守卫请闭眼。", "夜间")
        self._sleep_step(token, 0.8)

        with self.lock:
            deaths = set()
            if wolf_target and not saved and wolf_target != guard_target:
                deaths.add(wolf_target)
            if poison_target:
                deaths.add(poison_target)

            if not deaths:
                self._host_say("夜间行动结束，昨夜平安无事。", "夜间")
                self._log("系统", "夜晚平安无事")
                self._record("系统", "夜间结算", "无人死亡")
            else:
                for pid in list(deaths):
                    p = self._player_by_id(pid)
                    if p and p["alive"]:
                        self._handle_death(p, "夜间死亡", public=False)
                self._host_say("夜间行动结束，已记录夜间死亡信息。", "夜间")

    def _run_dawn(self, token):
        with self.lock:
            rd = self.state["round"]
            names = [e["player"] for e in self.state["elimination_order"] if e["round"] == rd and "夜间死亡" in e["reason"]]
            if names:
                line = "、".join(names)
                self._host_say(f"天亮了，昨夜死亡玩家：{line}。", "天亮")
                self._log("系统", f"第{rd}天亮：死亡 {line}")
                self._record("系统", "天亮", f"死亡：{line}")
                self._stage(f"天亮信息：{line}")
            else:
                self._host_say("天亮了，昨夜是平安夜。", "天亮")
                self._log("系统", f"第{rd}天亮：平安夜")
                self._record("系统", "天亮", "平安夜")
                self._stage("天亮信息：平安夜")
        self._sleep_step(token, 1)

    def _run_speech(self, token):
        with self.lock:
            order = [p["id"] for p in self._alive_players()]
            random.shuffle(order)
            self._host_say("进入发言阶段，请按顺序发言。", "发言")
            self._log("系统", "发言顺序：" + " -> ".join(self._name_of(pid) for pid in order))
            self._record("系统", "发言", "顺序：" + " -> ".join(self._name_of(pid) for pid in order))

        spoken_count = 0
        for pid in order:
            self._wait_if_paused(token)
            if not self._valid_to_run(token):
                return spoken_count
            speaker = None
            with self.lock:
                speaker = self._player_by_id(pid)
                if not speaker or not speaker["alive"]:
                    continue
            self._host_say(f"请 {speaker['name']} 发言。", "发言")
            try:
                speech_info = self._build_speech(speaker)
            except Exception:
                fallback = self._mock_speech(speaker, self._build_context(speaker))
                speech_info = {
                    "speech": fallback,
                    "claim": None,
                    "claim_text": "",
                    "thought_source": "虚拟(发言兜底)",
                    "speech_source": "虚拟(发言兜底)",
                }
            with self.lock:
                if not speaker["alive"]:
                    continue
                speaker["speeches"].append(
                    {"round": self.state["round"], "content": speech_info["speech"], "source": speech_info["speech_source"]}
                )
                self._log(speaker["name"], f"发言[来源:{speech_info['speech_source']}]：{speech_info['speech']}")
                self._record(speaker["name"], "发言", f"[来源:{speech_info['speech_source']}] {speech_info['speech']}")
                if speech_info["claim"]:
                    self.state["public_claims"].append(speech_info["claim"])
                    self._log("系统", f"{speaker['name']}公开信息：{speech_info['claim_text']}")
                    self._record("系统", "公开信息", f"{speaker['name']}：{speech_info['claim_text']}")
            spoken_count += 1
            self._sleep_step(token, 1.2)
        return spoken_count

    def _run_vote(self, token):
        with self.lock:
            alive = self._alive_players()
        self._host_say("进入投票阶段，请所有存活玩家依次投票。", "投票")
        tally = {}
        for voter in alive:
            self._wait_if_paused(token)
            if not self._valid_to_run(token):
                return
            vote_target_name = None
            with self.lock:
                if not voter["alive"]:
                    continue
                target = self._choose_vote_target(voter)
                if not target:
                    continue
                tally[target["id"]] = tally.get(target["id"], 0) + 1
                self.state["vote_stats"][voter["id"]] = self.state["vote_stats"].get(voter["id"], 0) + 1
                vote_target_name = target["name"]
            if vote_target_name:
                self._host_say(f"请 {voter['name']} 投票。", "投票")
                self._emit_thought(voter, "投票决策", f"基于当前信息，投票给 {vote_target_name}。")
                with self.lock:
                    self._log(voter["name"], f"投票给 {vote_target_name}")
                    self._record(voter["name"], "投票", f"-> {vote_target_name}")
            self._sleep_step(token, 0.7)

        with self.lock:
            if not tally:
                self._log("系统", "本轮无人被投出")
                self._record("系统", "投票结算", "无人出局")
                return
            maxv = max(tally.values())
            top = [pid for pid, c in tally.items() if c == maxv]
            out_id = random.choice(top)
            out_player = self._player_by_id(out_id)
            vote_line = "，".join([f"{self._name_of(pid)}({c})" for pid, c in tally.items()])
            self._log("系统", f"投票结果：{vote_line}")
            self._record("系统", "投票结算", vote_line)
            if out_player and out_player["alive"]:
                self._handle_death(out_player, f"白天投票出局（{maxv}票）")

    def _maybe_end_game(self, token):
        self._sleep_step(token, 0.4)
        with self.lock:
            alive = self._alive_players()
            wolves = len([p for p in alive if p["role"] == "wolf"])
            villagers = len([p for p in alive if p["role"] == "villager"])
            gods = len([p for p in alive if p["role"] in {"seer", "witch", "hunter", "guard"}])
            if wolves == 0:
                self._finish("好人")
                return True
            if villagers == 0 or gods == 0:
                self._finish("狼人")
                return True
            return False

    def _finish(self, winner):
        self.state["phase"] = "gameover"
        self.state["status"] = "ended"
        self.state["winner"] = winner
        for p in self.state["players"]:
            p["revealed"] = True
        elims = " -> ".join([f"{e['player']}({ROLE_META[e['role']]['label']})" for e in self.state["elimination_order"]]) or "无"
        summary = f"胜利阵营：{winner}\n总回合：{self.state['round']}\n淘汰顺序：{elims}"
        self._log("系统", f"游戏结束，{winner}阵营胜利")
        self._record("系统", "结束", summary)
        logger.info("game finished winner=%s round=%s", winner, self.state["round"])

    def _handle_death(self, player, reason, public=True):
        if not player["alive"]:
            return
        player["alive"] = False
        if self.state["settings"]["reveal_policy"] == "onDeath":
            player["revealed"] = True
        self.state["elimination_order"].append({
            "round": self.state["round"],
            "player": player["name"],
            "role": player["role"],
            "reason": reason,
        })
        self._log("系统", f"{player['name']} 出局，原因：{reason}", public=public)
        self._record(player["name"], "淘汰", f"{reason}，身份：{ROLE_META[player['role']]['label']}", public=public)

        if player["role"] == "hunter" and not player["abilities"]["shot_used"]:
            candidates = [p for p in self._alive_players() if p["id"] != player["id"]]
            if candidates:
                target = random.choice(candidates)
                player["abilities"]["shot_used"] = True
                self._log(player["name"], f"发动技能，带走 {target['name']}", public=public)
                self._record(player["name"], "技能", f"开枪带走 {target['name']}", public=public)
                self._handle_death(target, "被猎人带走", public=public)

    def _choose_seer_target(self, seer):
        checked = {x["target_id"] for x in seer["memory"]["seer_checks"]}
        candidates = [p for p in self._alive_players() if p["id"] != seer["id"] and p["id"] not in checked]
        if not candidates:
            candidates = [p for p in self._alive_players() if p["id"] != seer["id"]]
        return random.choice(candidates) if candidates else None

    def _choose_witch_action(self, witch, wolf_target):
        if witch["abilities"]["antidote"] and wolf_target:
            target = self._player_by_id(wolf_target)
            if target:
                chance = 0.78 if target["role"] in {"seer", "witch", "hunter", "guard"} else 0.45
                if random.random() < chance:
                    return {"type": "save"}
        if witch["abilities"]["poison"] and random.random() < 0.48:
            candidates = [p for p in self._alive_players() if p["id"] != witch["id"]]
            candidates.sort(key=lambda x: self._suspicion_score(x, witch), reverse=True)
            if candidates:
                return {"type": "poison", "target_id": candidates[0]["id"]}
        return {"type": "none"}

    def _choose_vote_target(self, voter):
        candidates = [p for p in self._alive_players() if p["id"] != voter["id"]]
        if not candidates:
            return None

        if voter["role"] == "wolf":
            good = [p for p in candidates if p["role"] != "wolf"]
            if good:
                good.sort(key=self._wolf_target_score, reverse=True)
                return good[0]

        if voter["role"] == "seer":
            known = [pid for pid in voter["memory"]["known_wolves"] if self._player_by_id(pid) and self._player_by_id(pid)["alive"]]
            if known:
                return self._player_by_id(known[0])

        claims = [c["target_id"] for c in self.state["public_claims"] if c.get("type") == "seer_result" and c.get("is_wolf")]
        for cid in claims:
            cp = self._player_by_id(cid)
            if cp and cp["alive"] and cp["id"] != voter["id"] and random.random() < 0.62:
                return cp

        candidates.sort(key=lambda x: self._suspicion_score(x, voter), reverse=True)
        return candidates[0]

    def _suspicion_score(self, target, observer):
        score = random.random() * 2
        speech = target["speeches"][-1]["content"] if target["speeches"] else ""
        if "保" in speech or "站边" in speech:
            score += 0.6
        if "我是预言家" in speech:
            score += 1.2
        claims = [c for c in self.state["public_claims"] if c.get("type") == "seer_result" and c.get("target_id") == target["id"] and c.get("is_wolf")]
        score += len(claims) * 2.2
        if observer["role"] == "wolf":
            if target["role"] != "wolf":
                score += 2
            if target["role"] in {"seer", "witch", "hunter", "guard"}:
                score += 1
        return score

    def _wolf_target_score(self, p):
        score = 0
        if p["role"] in {"seer", "witch", "hunter", "guard"}:
            score += 4
        if p["speeches"]:
            score += 1
        score += random.random() * 1.2
        return score

    def _build_speech(self, player):
        context = self._build_context(player)
        claim = None
        claim_text = ""
        if player["role"] == "seer" and player["memory"]["seer_checks"] and random.random() < 0.62:
            latest = player["memory"]["seer_checks"][-1]
            claim = {
                "type": "seer_result",
                "round": self.state["round"],
                "from_id": player["id"],
                "target_id": latest["target_id"],
                "is_wolf": latest["is_wolf"],
            }
            claim_text = f"查验 {self._name_of(latest['target_id'])} 为{'狼人' if latest['is_wolf'] else '好人'}"
            player["memory"]["claimed_seer"] = True

        same_round_speeches = [
            s["content"]
            for p in self.state["players"]
            for s in p.get("speeches", [])
            if s.get("round") == self.state["round"] and p.get("id") != player.get("id")
        ]
        thought, thought_source = self._generate_thought(player, "白天发言", context)
        speech, speech_source = self._generate_speech(player, context, claim_text, same_round_speeches)

        # Keep thought internal only; public channels should only show final speech content.
        self._add_thought(player, "白天发言", thought, thought_source)
        return {
            "speech": speech,
            "claim": claim,
            "claim_text": claim_text,
            "thought_source": thought_source,
            "speech_source": speech_source,
        }

    def _emit_thought(self, player, action, decision_line, extra_context=""):
        context = self._build_context(player)
        if extra_context:
            context = f"{context}，补充信息[{extra_context}]"
        thought, thought_source = self._generate_thought(player, action, context)
        merged = f"{thought}\n\n最终决定：{decision_line}"
        self._add_thought(player, action, merged, thought_source)

    def _add_thought(self, player, action, text, source):
        thought = {
            "id": f"{player['id']}_{int(time.time() * 1000)}_{random.randint(10, 999)}",
            "round": self.state["round"],
            "phase": self.state["phase"],
            "action": action,
            "text": text,
            "source": source,
            "ts": self._ts(),
        }
        player["history"].append(thought)
        secret = self._is_secret_action(action)
        self._log(player["name"], f"完成 {action}", public=not secret)
        # Do not write detailed thought content into public game records.
        self._record(player["name"], action, f"[来源:{source}] 思考已记录（后台）", public=not secret)

    def _is_secret_action(self, action):
        a = (action or "").strip()
        return a.startswith("夜间")

    def _generate_thought(self, player, action, context):
        provider = self.llm_config.get("provider", "mock")
        api_key = self.llm_config.get("api_key", "")
        if provider not in {"openai", "glm"} or not api_key:
            return self._mock_thought(player, action, context), "虚拟"
        action_timeout = 60
        base = self.llm_config.get("base_url", "https://api.openai.com/v1").rstrip("/")
        model_name = self.llm_config.get("model", "未知模型")
        prompt = "\n".join(
            [
                f"你是狼人杀AI，当前身份：{ROLE_META[player['role']]['label']}。",
                f"当前行动：{action}",
                "请用简洁中文给出结构化思考，包含：已知信息、角色立场、决策分析、行动决定。",
                f"上下文：{context}",
            ]
        )
        try:
            with self.lock:
                self.state["llm_live"] = {
                    "active": True,
                    "player_id": player.get("id"),
                    "player_name": player.get("name"),
                    "action": action,
                    "source": model_name,
                    "text": "正在请求模型结果...",
                }
                self._mark_updated_locked()
            text, err = self._fetch_chat_text_non_stream(
                base_url=base,
                api_key=api_key,
                payload={
                    "model": model_name,
                    "temperature": self.llm_config.get("temperature", 0.7),
                    "messages": [
                        {"role": "system", "content": "你是一个狼人杀对局中的理性AI。输出简洁且逻辑清晰。"},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 320,
                },
                timeout=action_timeout,
            )

            with self.lock:
                self.state["llm_live"] = None
                self._mark_updated_locked()

            if err:
                return self._mock_thought(player, action, context), err
            if text and text.strip():
                return text.strip()[:320], model_name
            return self._mock_thought(player, action, context), "虚拟(模型返回空内容)"
        except Exception as exc:
            err = f"{type(exc).__name__}:{str(exc)}".strip()
            err = err[:120] if err else "unknown"
            with self.lock:
                self.state["llm_live"] = None
                self._mark_updated_locked()
            return self._mock_thought(player, action, context), f"虚拟(模型调用异常:{err})"

    def _mock_thought(self, player, action, context):
        role_view = f"我是{ROLE_META[player['role']]['label']}，目标是{'压缩好人空间' if player['role'] == 'wolf' else '找出狼人'}。"
        analysis_map = {
            "夜间袭击": "优先处理高影响神职或能组织票型的玩家，降低白天反推强度。",
            "夜间查验": "优先查验发言强势但站位摇摆的玩家，提高白天信息密度。",
            "夜间用药": "药剂资源有限，只有在收益明显时才使用。",
            "夜间守护": "守护重点放在关键神职和可能被集火位。",
            "白天发言": "发言需要制造可信度，同时为投票阶段铺垫。",
            "投票决策": "投票必须与公开信息和个人立场一致，避免自相矛盾。",
        }
        analysis = analysis_map.get(action, "基于当前局面选择最稳健策略。")
        return "\n".join(
            [
                f"已知信息：{context[:76]}",
                f"角色立场：{role_view}",
                f"决策分析：{analysis}",
                f"行动决定：执行{action}。",
            ]
        )

    def _mock_speech(self, player, context):
        alive = [p for p in self._alive_players() if p["id"] != player["id"]]
        alive_sorted = sorted(alive, key=lambda p: self._suspicion_score(p, player), reverse=True)
        top1 = alive_sorted[0]["name"] if len(alive_sorted) > 0 else "前置位"
        top2 = alive_sorted[1]["name"] if len(alive_sorted) > 1 else top1
        latest_claims = [c for c in self.state.get("public_claims", []) if c.get("round") == self.state["round"]]
        claim_brief = "、".join(
            [f"{self._name_of(c.get('from_id'))}说{self._name_of(c.get('target_id'))}是{'狼' if c.get('is_wolf') else '好'}" for c in latest_claims[:2]]
        )

        opener_pool = [
            "我先说下我这轮的感受，",
            "先别急着上票，我先把我听下来的点讲一下，",
            "我这边先给个中间结论，后面你们可以拍我，",
            "这一轮我不想空发言，直接给判断，",
        ]
        transition_pool = [
            "有点不对劲的是",
            "我最在意的是",
            "我现在卡住的点在",
            "如果要盘逻辑，我会先看",
        ]
        close_pool = [
            "我这一票大概率会落在",
            "目前我会优先投",
            "这轮先处理",
            "先出",
        ]

        role_tone = {
            "wolf": f"{top1}和{top2}这两个位置都在抢节奏，但落点一直在飘。",
            "seer": f"我更看重可验证信息，{top1}这个位置和已知信息的贴合度很低。",
            "witch": f"夜里信息和白天站位对不上，{top1}这里前后说法不连贯。",
            "hunter": f"我先把枪口预留给高冲突位，{top1}现在像是想把局面搅混。",
            "guard": f"站位稳定性最差的是{top1}，其次是{top2}，这两位要重点盯。",
            "villager": f"我作为民牌只看逻辑闭环，{top1}这个点目前闭不上。",
        }

        extra_claim = f"另外场上现在有信息：{claim_brief}。" if claim_brief else "场上暂时没形成统一信息口径。"
        hedge = random.choice(["我可能有偏差，后置位可以补充。", "这是我当前最稳的视角。", "如果有新信息我会立刻修正。"])

        return " ".join(
            [
                random.choice(opener_pool),
                f"{random.choice(transition_pool)}{role_tone[player['role']]}",
                extra_claim,
                f"{random.choice(close_pool)}{top1}。",
                hedge,
            ]
        )

    def _generate_speech(self, player, context, claim_text, existing_speeches):
        provider = self.llm_config.get("provider", "mock")
        api_key = self.llm_config.get("api_key", "")
        base_speech = self._mock_speech(player, context)
        if claim_text:
            base_speech = f"我是预言家，{claim_text}。{base_speech}"

        if provider not in {"openai", "glm"} or not api_key:
            logger.info("speech fallback mock: provider=%s api_key_present=%s player=%s", provider, bool(api_key), player.get("name"))
            return self._dedupe_speech(base_speech, existing_speeches, player), "虚拟"

        base = self.llm_config.get("base_url", "https://api.openai.com/v1").rstrip("/")
        model_name = self.llm_config.get("model", "未知模型")
        safe_history = [self._clip_speech_for_prompt(x) for x in existing_speeches if isinstance(x, str) and x.strip()]
        unique_guard = " | ".join(safe_history[-4:]) if safe_history else "暂无"
        prompt = "\n".join(
            [
                f"你在狼人杀里当前身份是{ROLE_META[player['role']]['label']}，请说一段自然口语化中文发言。",
                "要求：像真人对局说话，2-4句，避免模板腔，给出明确投票倾向。",
                "只输出发言正文，不要标题、标签、解释。",
                "必须避免与已有发言重复或高度相似。",
                f"已有发言（避免重复）：{unique_guard}",
                f"局面上下文：{context}",
                f"如需要可包含信息：{claim_text or '无'}",
                "发言要像真实玩家临场表达，不要复述规则。",
            ]
        )
        text, err = self._fetch_chat_text_non_stream(
            base_url=base,
            api_key=api_key,
            payload={
                "model": model_name,
                "temperature": min(0.5, self.llm_config.get("temperature", 0.7)),
                "messages": [
                    {"role": "system", "content": "你是狼人杀玩家，说话像真人，不要书面模板。"},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 220,
            },
            timeout=60,
        )
        if text and text.strip():
            speech = self._trim_llm_speech_output(text)
            logger.debug(
                "speech llm raw_len=%s trimmed_len=%s player=%s model=%s",
                len(text),
                len(speech),
                player.get("name"),
                model_name,
            )
            speech = self._dedupe_speech(speech, existing_speeches, player)
            if not self._normalize_speech(speech):
                fallback = self._dedupe_speech(self._mock_speech(player, context), existing_speeches, player)
                logger.warning("speech fallback empty-after-sanitize player=%s", player.get("name"))
                return self._ensure_non_empty_speech(fallback, player, context, existing_speeches), "虚拟(发言为空兜底)"
            logger.info("speech llm success player=%s model=%s len=%s", player.get("name"), model_name, len(speech))
            return self._ensure_non_empty_speech(speech, player, context, existing_speeches), model_name

        source = err if err else "虚拟(发言模型为空)"
        logger.warning("speech llm empty player=%s source=%s", player.get("name"), source)
        fallback = self._dedupe_speech(base_speech, existing_speeches, player)
        return self._ensure_non_empty_speech(fallback, player, context, existing_speeches), source

    def _dedupe_speech(self, speech, existing_speeches, player):
        for old in existing_speeches[-8:]:
            if self._is_same_or_too_similar(speech, old):
                target_obj = self._choose_vote_target(player)
                target = self._name_of(target_obj["id"]) if target_obj else "前置位"
                marker = random.choice(["这轮我会更激进一点。", "我先把票型做实。", "我愿意为这票负责。"])
                return f"{speech} 我补一句，这轮我更明确会投 {target}。{marker}"
        return speech

    def _normalize_speech(self, text):
        return "".join(ch for ch in (text or "").lower() if ch not in " ，。！？；：、,.!?;:()[]{}\"'“”‘’\n\r\t")

    def _clip_speech_for_prompt(self, text, max_len=90):
        s = self._sanitize_speech_output(text or "")
        return s[:max_len]

    def _sanitize_speech_output(self, text):
        s = (text or "").strip()
        # Strip markup/control prefixes, but keep the semantic text whenever possible.
        bad_prefixes = ["分析请求", "角色：", "语气：", "长度：", "内容：", "约束：", "避免重复："]
        lines = []
        for ln in s.splitlines():
            l = ln.strip()
            if not l:
                continue
            # remove common markdown bullets/numbering instead of dropping whole line
            l = re.sub(r"^[-*]\s+", "", l)
            l = re.sub(r"^\d+[.)]\s+", "", l)
            if any(l.startswith(p) for p in bad_prefixes):
                # keep content after first colon if possible
                if "：" in l:
                    l = l.split("：", 1)[1].strip()
                elif ":" in l:
                    l = l.split(":", 1)[1].strip()
                else:
                    continue
            if l:
                lines.append(l)
        cleaned = " ".join(lines).strip()
        # If model wrapped output with quotes/code fences.
        cleaned = cleaned.replace("```", "").replace("`", "").strip()
        return cleaned

    def _trim_llm_speech_output(self, text):
        s = self._sanitize_speech_output(text or "")
        if not s:
            return ""
        # Keep only a short spoken segment (2-4 sentences) and drop obvious meta tails.
        hard_cut_keys = [
            "分析请求", "角色：", "语气：", "长度：", "内容：", "约束：", "避免重复：",
            "用户是在要求", "我明白了", "只输出", "不要输出", "提示词", "system", "assistant",
        ]
        for key in hard_cut_keys:
            idx = s.lower().find(key.lower())
            if idx >= 0:
                s = s[:idx].strip()
        parts = [p.strip() for p in re.split(r"[。！？!?]", s) if p and p.strip()]
        meta_frag = (
            "分析用户请求", "分析请求", "角色", "语气", "长度", "内容", "约束", "避免重复",
            "只输出", "不要输出", "提示词", "system", "assistant", "上下文",
        )
        parts = [p for p in parts if not any(k.lower() in p.lower() for k in meta_frag)]
        if not parts:
            return s[:120].strip()
        keep = parts[:4]
        out = "。".join(keep).strip()
        if out and not out.endswith("。"):
            out += "。"
        return out

    def _repair_meta_speech(self, speech, player, context, existing_speeches):
        s = (speech or "").strip()
        if not s:
            return ""
        # Remove common leaked meta prompt segments but keep potentially valid spoken text.
        s = re.sub(r"[*_`>#\[\]]", "", s)
        cut_keys = [
            "分析请求",
            "角色：",
            "语气：",
            "长度：",
            "内容：",
            "约束：",
            "避免重复：",
            "只输出玩家要说的话",
            "不要输出思考过程",
            "用户是在要求",
            "我明白了",
            "最近事件",
            "已有发言",
        ]
        for key in cut_keys:
            idx = s.find(key)
            if idx >= 0:
                s = s[:idx]
        # Keep first 1-2 natural spoken sentences.
        parts = [x.strip() for x in re.split(r"[。！？!?]", s) if x and x.strip()]
        kept = []
        bad_frag = ("提示", "系统", "分析", "请求", "角色", "语气", "长度", "约束", "输出", "模型", "上下文")
        for p in parts:
            if any(k in p for k in bad_frag):
                continue
            kept.append(p)
            if len(kept) >= 2:
                break
        repaired = "。".join(kept).strip()
        if repaired:
            repaired = f"{repaired}。"
            repaired = self._dedupe_speech(repaired, existing_speeches, player)
            if self._normalize_speech(repaired) and not self._is_meta_or_prompt_leak(repaired):
                logger.info("speech repaired-from-meta player=%s len=%s", player.get("name"), len(repaired))
                return repaired
        return ""

    def _extract_spoken_candidate_from_leak(self, speech):
        s = self._sanitize_speech_output(speech or "")
        if not s:
            return ""
        # Keep sentence fragments that look like actual table talk.
        segments = [x.strip() for x in re.split(r"[。！？!?]", s) if x and x.strip()]
        bad_tokens = (
            "分析请求", "角色", "语气", "长度", "内容", "约束", "避免重复", "提示词", "system", "assistant",
            "输出", "用户是在要求", "我明白了", "请只", "不要输出", "最近事件", "已有发言",
        )
        kept = []
        for seg in segments:
            lower = seg.lower()
            if any(t.lower() in lower for t in bad_tokens):
                continue
            kept.append(seg)
            if len(kept) >= 3:
                break
        if not kept:
            return ""
        out = "。".join(kept).strip()
        if out and not out.endswith("。"):
            out += "。"
        return out

    def _rescue_speech_with_llm(self, base, api_key, model_name, leaked_text, context, role_label):
        raw = (leaked_text or "").strip()[:520]
        repair_prompt = "\n".join(
            [
                f"你是狼人杀玩家，身份{role_label}。",
                "请直接生成2-4句中文口语发言，给出明确投票倾向。",
                "只输出发言正文，不要任何标签或解释。",
                f"局面：{context}",
                f"可参考片段：{raw or '无'}",
            ]
        )
        text_fix, err_fix = self._fetch_chat_text_non_stream(
            base_url=base,
            api_key=api_key,
            payload={
                "model": model_name,
                "temperature": 0.35,
                "messages": [
                    {"role": "system", "content": "你是狼人杀玩家，只输出发言正文。"},
                    {"role": "user", "content": repair_prompt},
                ],
                "max_tokens": 180,
            },
            timeout=35,
        )
        if err_fix:
            logger.info("speech rescue pass1 failed model=%s err=%s", model_name, err_fix)
        else:
            fixed = (text_fix or "").strip()
            if fixed:
                return fixed

        # Last chance: do not feed noisy context, ask for a short clean spoken line directly.
        short_prompt = "\n".join(
            [
                f"你在狼人杀中身份是{role_label}。",
                "只写2-3句玩家口语发言，最后一句必须明确投票给某人。",
                "不要标题、不要解释、不要条目、不要括号说明。",
            ]
        )
        text_fix2, err_fix2 = self._fetch_chat_text_non_stream(
            base_url=base,
            api_key=api_key,
            payload={
                "model": model_name,
                "temperature": 0.45,
                "messages": [
                    {"role": "system", "content": "狼人杀玩家发言生成器。只输出发言正文。"},
                    {"role": "user", "content": short_prompt},
                ],
                "max_tokens": 120,
            },
            timeout=28,
        )
        if err_fix2:
            logger.info("speech rescue pass2 failed model=%s err=%s", model_name, err_fix2)
            return ""
        return (text_fix2 or "").strip()

    def _is_meta_or_prompt_leak(self, speech):
        s = (speech or "").lower()
        leak_keys = [
            "分析请求", "角色：", "语气：", "长度：", "内容：", "约束：", "避免重复",
            "提示词", "system", "assistant", "用户是在要求", "我明白了", "只输出玩家要说的话",
            "只输出发言正文", "不要输出思考过程", "请直接生成2-4句",
        ]
        if any(k.lower() in s for k in leak_keys):
            return True
        # Heuristic: markdown/analysis structure is likely leak.
        if ("**" in speech) or ("```" in speech):
            return True
        return False

    def _is_same_or_too_similar(self, a, b):
        na = self._normalize_speech(a)
        nb = self._normalize_speech(b)
        if not na or not nb:
            return False
        if na == nb:
            return True
        sim = SequenceMatcher(None, na, nb).ratio()
        return sim >= 0.86

    def _is_speech_too_similar(self, speech, existing_speeches):
        for old in existing_speeches[-8:]:
            if self._is_same_or_too_similar(speech, old):
                return True
        return False

    def _ensure_non_empty_speech(self, speech, player, context, existing_speeches):
        if self._normalize_speech(speech):
            return speech
        fallback = self._dedupe_speech(self._mock_speech(player, context), existing_speeches, player)
        if self._normalize_speech(fallback):
            logger.warning("speech hard-fallback mock player=%s", player.get("name"))
            return fallback
        logger.error("speech hard-fallback constant player=%s", player.get("name"))
        return f"我先给结论，这轮我先投 {self._name_of(self._choose_vote_target(player)['id']) if self._choose_vote_target(player) else '前置位'}。"

    def _build_context(self, player):
        alive = "、".join(p["name"] for p in self._alive_players())
        dead = "、".join(p["name"] for p in self.state["players"] if not p["alive"]) or "暂无"
        recent = " | ".join(f"{x['actor']}:{x['text']}" for x in self.state["logs"][-3:])
        return f"回合{self.state['round']}，存活[{alive}]，死亡[{dead}]，最近事件[{recent}]，我的身份[{ROLE_META[player['role']]['label']}]"

    def _post_chat_completions(self, base_url, api_key, payload, timeout):
        # Use ASCII-only JSON to avoid any latin-1 fallback issues in upstream stacks.
        body = json.dumps(payload, ensure_ascii=True).encode("ascii")
        return requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json; charset=utf-8",
            },
            data=body,
            timeout=timeout,
        )

    def _stream_chat_text(self, base_url, api_key, payload, timeout, on_chunk):
        body = json.dumps(payload, ensure_ascii=True).encode("ascii")
        try:
            resp = requests.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json; charset=utf-8",
                    "Accept": "text/event-stream",
                },
                data=body,
                timeout=timeout,
                stream=True,
            )
        except requests.ReadTimeout:
            return "", "虚拟(流式读取超时)"
        except Exception as exc:
            return "", f"虚拟(流式异常:{type(exc).__name__})"
        if not resp.ok:
            return "", f"虚拟(HTTP {resp.status_code})"

        full = ""
        start_ts = time.time()
        last_delta_ts = start_ts
        idle_timeout = min(20, max(8, timeout // 3))
        max_duration = timeout
        stop_reason = None

        try:
            for raw_line in resp.iter_lines(decode_unicode=True):
                now = time.time()
                if now - start_ts > max_duration:
                    stop_reason = "总时长超时"
                    break
                if now - last_delta_ts > idle_timeout:
                    stop_reason = "流式空转超时"
                    break
                if not raw_line:
                    continue
                line = raw_line.strip()
                if not line.startswith("data:"):
                    continue
                data_part = line[5:].strip()
                if data_part == "[DONE]":
                    break
                try:
                    data = json.loads(data_part)
                except Exception:
                    continue
                delta = self._extract_stream_delta_text(data)
                if delta:
                    full += delta
                    last_delta_ts = time.time()
                    on_chunk(full)
        except requests.ReadTimeout:
            return "", "虚拟(流式读取超时)"
        except Exception as exc:
            return "", f"虚拟(流式异常:{type(exc).__name__})"
        if full:
            return full, None
        if stop_reason:
            return "", f"虚拟({stop_reason})"
        return "", "虚拟(模型返回空内容:流式为空)"

    def _fetch_chat_text_non_stream(self, base_url, api_key, payload, timeout):
        with self.lock:
            m = self.state.get("llm_metrics", {})
            m["requests"] = int(m.get("requests", 0)) + 1
            m["last_at"] = self._ts()
            m["last_status"] = "requesting"
            m["last_error"] = ""
            self.state["llm_metrics"] = m
            self._mark_updated_locked()
        logger.info("llm request model=%s timeout=%ss", payload.get("model"), timeout)
        resp = self._post_chat_completions(
            base_url=base_url,
            api_key=api_key,
            payload=payload,
            timeout=timeout,
        )
        if not resp.ok:
            logger.warning("llm response failed status=%s model=%s", resp.status_code, payload.get("model"))
            with self.lock:
                m = self.state.get("llm_metrics", {})
                m["failed"] = int(m.get("failed", 0)) + 1
                m["last_status"] = f"HTTP {resp.status_code}"
                m["last_error"] = (resp.text or "")[:180]
                m["last_at"] = self._ts()
                self.state["llm_metrics"] = m
                self._mark_updated_locked()
            return "", f"虚拟(补拉HTTP {resp.status_code})"
        try:
            data = resp.json()
        except Exception as exc:
            logger.warning("llm json decode failed model=%s err=%s", payload.get("model"), type(exc).__name__)
            with self.lock:
                m = self.state.get("llm_metrics", {})
                m["failed"] = int(m.get("failed", 0)) + 1
                m["last_status"] = "json_error"
                m["last_error"] = f"{type(exc).__name__}:{str(exc)[:120]}"
                m["last_at"] = self._ts()
                self.state["llm_metrics"] = m
                self._mark_updated_locked()
            return "", f"虚拟(补拉解析异常:{type(exc).__name__})"
        text = self._extract_text_from_chat_response(data)
        if text:
            logger.info("llm success model=%s chars=%s", payload.get("model"), len(text))
            with self.lock:
                m = self.state.get("llm_metrics", {})
                m["success"] = int(m.get("success", 0)) + 1
                m["last_status"] = "ok"
                m["last_error"] = ""
                m["last_at"] = self._ts()
                self.state["llm_metrics"] = m
                self._mark_updated_locked()
            return text, None
        logger.warning("llm empty response model=%s", payload.get("model"))
        with self.lock:
            m = self.state.get("llm_metrics", {})
            m["failed"] = int(m.get("failed", 0)) + 1
            m["last_status"] = "empty"
            m["last_error"] = self._diagnose_empty_chat_response(data)[:180]
            m["last_at"] = self._ts()
            self.state["llm_metrics"] = m
            self._mark_updated_locked()
        return "", f"虚拟(补拉为空:{self._diagnose_empty_chat_response(data)})"

    def _update_live_text(self, player_id, action, source, text):
        with self.lock:
            live = self.state.get("llm_live")
            if not isinstance(live, dict):
                self.state["llm_live"] = {
                    "active": True,
                    "player_id": player_id,
                    "action": action,
                    "source": source,
                    "text": text,
                }
            else:
                live["active"] = True
                live["player_id"] = player_id
                live["action"] = action
                live["source"] = source
                live["text"] = text
            self._mark_updated_locked()

    def _load_llm_config_from_disk(self):
        if not self.config_file.exists():
            return
        try:
            data = json.loads(self.config_file.read_text(encoding="utf-8"))
        except Exception:
            return
        if not isinstance(data, dict):
            return
        self.llm_config["provider"] = data.get("provider", self.llm_config["provider"])
        self.llm_config["model"] = data.get("model", self.llm_config["model"])
        self.llm_config["temperature"] = max(0, min(2, float(data.get("temperature", self.llm_config["temperature"]))))
        self.llm_config["base_url"] = data.get("base_url", self.llm_config["base_url"])
        self.llm_config["api_key"] = data.get("api_key", self.llm_config["api_key"])

    def _save_llm_config_to_disk(self):
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(json.dumps(self.llm_config, ensure_ascii=False, indent=2), encoding="utf-8")

    def _extract_text_from_chat_response(self, data):
        if not isinstance(data, dict):
            return ""
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""
        c0 = choices[0] if isinstance(choices[0], dict) else {}
        message = c0.get("message", {}) if isinstance(c0.get("message"), dict) else {}
        content = message.get("content", "")

        if isinstance(content, str):
            txt = content.strip()
            if txt:
                return txt
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    txt = item.get("text")
                    if isinstance(txt, str):
                        parts.append(txt)
                    alt = item.get("content")
                    if isinstance(alt, str):
                        parts.append(alt)
            merged = "".join(parts).strip()
            if merged:
                return merged
        reasoning = message.get("reasoning_content", "")
        if isinstance(reasoning, str):
            return reasoning.strip()
        if isinstance(reasoning, list):
            parts = []
            for item in reasoning:
                if isinstance(item, dict):
                    txt = item.get("text")
                    if isinstance(txt, str):
                        parts.append(txt)
                    alt = item.get("content")
                    if isinstance(alt, str):
                        parts.append(alt)
            merged = "".join(parts).strip()
            if merged:
                return merged
        if isinstance(c0.get("text"), str):
            txt = c0.get("text").strip()
            if txt:
                return txt
        if isinstance(data.get("output_text"), str):
            txt = data.get("output_text").strip()
            if txt:
                return txt
        return ""

    def _diagnose_empty_chat_response(self, data):
        if not isinstance(data, dict):
            return "响应不是JSON对象"
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            return "缺少choices"
        c0 = choices[0] if isinstance(choices[0], dict) else {}
        finish_reason = c0.get("finish_reason", "unknown")
        msg = c0.get("message", {}) if isinstance(c0.get("message"), dict) else {}

        candidates = []
        if isinstance(c0.get("text"), str) and c0.get("text").strip():
            candidates.append("choice.text")
        if isinstance(msg.get("content"), str) and msg.get("content").strip():
            candidates.append("message.content(str)")
        if isinstance(msg.get("content"), list):
            non_empty = any(
                isinstance(x, dict)
                and (
                    (isinstance(x.get("text"), str) and x.get("text").strip())
                    or (isinstance(x.get("content"), str) and x.get("content").strip())
                )
                for x in msg.get("content")
            )
            if non_empty:
                candidates.append("message.content(list)")
        if isinstance(msg.get("reasoning_content"), str) and msg.get("reasoning_content").strip():
            candidates.append("message.reasoning_content(str)")
        if isinstance(msg.get("reasoning_content"), list) and msg.get("reasoning_content"):
            candidates.append("message.reasoning_content(list)")
        if isinstance(data.get("output_text"), str) and data.get("output_text").strip():
            candidates.append("output_text")

        usage = "usage" if isinstance(data.get("usage"), dict) and data.get("usage") else "no-usage"
        if candidates:
            return f"finish={finish_reason};可见字段={','.join(candidates)};{usage}"
        msg_keys = ",".join(msg.keys()) if msg else "none"
        return f"finish={finish_reason};message_keys={msg_keys};{usage}"

    def _extract_stream_delta_text(self, data):
        if not isinstance(data, dict):
            return ""
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""
        c0 = choices[0] if isinstance(choices[0], dict) else {}
        delta = c0.get("delta", {}) if isinstance(c0.get("delta"), dict) else {}

        content = delta.get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    txt = item.get("text")
                    if isinstance(txt, str):
                        parts.append(txt)
                    alt = item.get("content")
                    if isinstance(alt, str):
                        parts.append(alt)
            if parts:
                return "".join(parts)

        reasoning = delta.get("reasoning_content", "")
        if isinstance(reasoning, str):
            return reasoning
        if isinstance(reasoning, list):
            parts = []
            for item in reasoning:
                if isinstance(item, dict):
                    txt = item.get("text")
                    if isinstance(txt, str):
                        parts.append(txt)
                    alt = item.get("content")
                    if isinstance(alt, str):
                        parts.append(alt)
            if parts:
                return "".join(parts)

        # Compatibility fallback: some providers emit chunks in `message` instead of `delta`.
        message = c0.get("message", {}) if isinstance(c0.get("message"), dict) else {}
        msg_content = message.get("content", "")
        if isinstance(msg_content, str):
            return msg_content
        if isinstance(msg_content, list):
            parts = []
            for item in msg_content:
                if isinstance(item, dict):
                    txt = item.get("text")
                    if isinstance(txt, str):
                        parts.append(txt)
                    alt = item.get("content")
                    if isinstance(alt, str):
                        parts.append(alt)
            if parts:
                return "".join(parts)

        msg_reasoning = message.get("reasoning_content", "")
        if isinstance(msg_reasoning, str):
            return msg_reasoning
        if isinstance(msg_reasoning, list):
            parts = []
            for item in msg_reasoning:
                if isinstance(item, dict):
                    txt = item.get("text")
                    if isinstance(txt, str):
                        parts.append(txt)
                    alt = item.get("content")
                    if isinstance(alt, str):
                        parts.append(alt)
            if parts:
                return "".join(parts)
        return ""

    def _alive_players(self):
        return [p for p in self.state["players"] if p["alive"]]

    def _find_alive_role(self, role):
        for p in self.state["players"]:
            if p["alive"] and p["role"] == role:
                return p
        return None

    def _player_by_id(self, pid):
        for p in self.state["players"]:
            if p["id"] == pid:
                return p
        return None

    def _name_of(self, pid):
        p = self._player_by_id(pid)
        return p["name"] if p else "未知"

    def _host_say(self, text, phase_label=None, public=True):
        with self.lock:
            phase = phase_label or PHASE_NAME.get(self.state.get("phase"), self.state.get("phase"))
            self._log("主持人", text, public=public)
            self._record("主持人", phase, text, public=public)

    def _log(self, actor, text, public=True):
        if not public:
            return
        self.state["logs"].append({
            "actor": actor,
            "text": text,
            "round": self.state["round"],
            "phase": self.state["phase"],
            "ts": self._ts(),
        })
        self.state["logs"] = self.state["logs"][-500:]
        self._mark_updated_locked()

    def _record(self, actor, phase, note, public=True):
        if not public:
            return
        self.state["records"].append({
            "round": self.state["round"],
            "actor": actor,
            "phase": phase,
            "note": note,
            "ts": self._ts(),
        })
        self.state["records"] = self.state["records"][-1200:]
        self._mark_updated_locked()

    def _stage(self, text):
        self.state["stage_lines"].append(text)
        self.state["stage_lines"] = self.state["stage_lines"][-6:]
        self._mark_updated_locked()

    def _valid_to_run(self, token):
        with self.lock:
            return token == self.run_token and self.state["status"] in {"running", "paused"} and self.state["winner"] is None

    def _wait_if_paused(self, token):
        while True:
            with self.lock:
                if token != self.run_token:
                    return
                if self.state["status"] != "paused":
                    return
            time.sleep(0.12)

    def _sleep_step(self, token, units):
        ms = SPEED_SEC.get(self.state["settings"].get("speed", "normal"), 0.56) * units
        end = time.time() + ms
        while time.time() < end:
            if not self._valid_to_run(token):
                return
            self._wait_if_paused(token)
            time.sleep(0.08)

    def _ts(self):
        return datetime.now().strftime("%H:%M:%S")


BASE_DIR = Path(__file__).resolve().parent.parent
app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")
engine = GameEngine()


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/api/state")
def api_state():
    logger.debug("api state")
    return jsonify(engine.snapshot())


@app.get("/api/events")
def api_events():
    last = request.args.get("last", default=-1, type=int)

    def stream():
        first = engine.snapshot()
        current = first.get("revision", -1)
        yield f"event: state\ndata: {json.dumps(first, ensure_ascii=False)}\n\n"

        while True:
            updated = engine.wait_for_update(current, timeout=25)
            if updated is None:
                yield ": keepalive\n\n"
                continue
            current = updated.get("revision", current)
            yield f"event: state\ndata: {json.dumps(updated, ensure_ascii=False)}\n\n"

    return Response(
        stream(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@app.post("/api/config/game")
def api_config_game():
    payload = request.get_json(silent=True) or {}
    ok, msg = engine.configure_game(payload)
    logger.info("api config game ok=%s msg=%s", ok, msg)
    return jsonify({"ok": ok, "message": msg, "state": engine.snapshot()})


@app.post("/api/config/llm")
def api_config_llm():
    payload = request.get_json(silent=True) or {}
    engine.configure_llm(payload)
    ok, message = engine.validate_llm_config()
    logger.info("api config llm ok=%s message=%s", ok, message)
    return jsonify({"ok": ok, "message": message, "state": engine.snapshot()})


@app.post("/api/game/start")
def api_start():
    payload = request.get_json(silent=True) or {}
    if payload:
        engine.configure_game(payload)
    engine.start()
    logger.info("api game start")
    return jsonify({"ok": True, "state": engine.snapshot()})


@app.post("/api/game/pause")
def api_pause():
    engine.pause()
    logger.info("api game pause")
    return jsonify({"ok": True, "state": engine.snapshot()})


@app.post("/api/game/resume")
def api_resume():
    engine.resume()
    logger.info("api game resume")
    return jsonify({"ok": True, "state": engine.snapshot()})


@app.post("/api/game/reset")
def api_reset():
    engine.reset()
    logger.info("api game reset")
    return jsonify({"ok": True, "state": engine.snapshot()})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
