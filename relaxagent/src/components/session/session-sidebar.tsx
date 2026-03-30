"use client";

import Link from "next/link";
import { useState } from "react";
import { createRemoteSession, deleteRemoteSession } from "@/lib/api";
import { sessionSnapshotToChatSession } from "@/lib/chat";
import { cn, formatTimestamp } from "@/lib/utils";
import { useAgentStore, useSelectedAgent } from "@/store/use-agent-store";
import { useChatStore } from "@/store/use-chat-store";

export function SessionSidebar() {
  const sessions = useChatStore((state) => state.sessions);
  const activeSessionId = useChatStore((state) => state.activeSessionId);
  const createSession = useChatStore((state) => state.createSession);
  const insertSession = useChatStore((state) => state.insertSession);
  const setActiveSession = useChatStore((state) => state.setActiveSession);
  const deleteSession = useChatStore((state) => state.deleteSession);
  const renameSession = useChatStore((state) => state.renameSession);
  const setError = useChatStore((state) => state.setError);
  const agents = useAgentStore((state) => state.agents);
  const selectedAgentId = useAgentStore((state) => state.selectedAgentId);
  const setSelectedAgentId = useAgentStore((state) => state.setSelectedAgentId);
  const selectedAgent = useSelectedAgent();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftTitle, setDraftTitle] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);

  async function handleCreateSession() {
    if (isCreating) {
      return;
    }

    if (!selectedAgent) {
      setError("当前没有可用 Agent，请稍后刷新重试。");
      return;
    }

    const sessionId = createSession(selectedAgent.id, selectedAgent.name);
    setIsCreating(true);
    setError(null);

    try {
      const remoteSession = await createRemoteSession(sessionId, selectedAgent.id, "新会话");
      insertSession(
        sessionSnapshotToChatSession(remoteSession, 0, undefined, selectedAgent.name)
      );
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : "创建会话失败。";
      deleteSession(sessionId);
      setError(message);
    } finally {
      setIsCreating(false);
    }
  }

  async function handleDeleteSession(sessionId: string) {
    if (deletingSessionId) {
      return;
    }

    setDeletingSessionId(sessionId);
    setError(null);

    try {
      await deleteRemoteSession(sessionId);
      deleteSession(sessionId);
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : "删除会话失败。";
      setError(message);
    } finally {
      setDeletingSessionId(null);
    }
  }

  return (
    <aside className="flex h-full min-h-0 w-full flex-col overflow-hidden border-r border-black/10 bg-white/80 backdrop-blur">
      <div className="border-b border-black/10 px-4 py-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-slate-500">RelaxAgent</p>
            <h1 className="text-lg font-semibold text-slate-900">Simple LobeHub</h1>
          </div>
          <Link
            href="/settings"
            className="rounded-full border border-black/10 px-3 py-1.5 text-sm text-slate-700 transition hover:border-black/20 hover:bg-slate-100"
          >
            设置
          </Link>
        </div>
        <button
          type="button"
          onClick={() => void handleCreateSession()}
          disabled={isCreating || agents.length === 0}
          className="mt-4 w-full rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-700"
        >
          {isCreating ? "创建中..." : "新建会话"}
        </button>
        <div className="mt-3">
          <label className="mb-2 block text-xs uppercase tracking-[0.2em] text-slate-400">
            新会话 Agent
          </label>
          <select
            value={selectedAgentId ?? selectedAgent?.id ?? ""}
            onChange={(event) => setSelectedAgentId(event.target.value)}
            className="w-full rounded-2xl border border-black/10 bg-white px-3 py-3 text-sm text-slate-700 outline-none"
          >
            {agents.map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.name}
              </option>
            ))}
          </select>
          {selectedAgent ? (
            <p className="mt-2 text-xs leading-5 text-slate-500">{selectedAgent.description}</p>
          ) : null}
        </div>
      </div>

      <div className="min-h-0 flex-1 space-y-2 overflow-y-auto px-3 py-3">
        {sessions.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-black/10 bg-white px-4 py-5 text-sm leading-6 text-slate-500">
            还没有会话，先创建一个开始聊天吧。
          </div>
        ) : null}

        {sessions.map((session) => {
          const isActive = session.id === activeSessionId;
          const isEditing = session.id === editingId;

          return (
            <div
              key={session.id}
              className={cn(
                "rounded-3xl border px-3 py-3 transition",
                isActive
                  ? "border-slate-900 bg-slate-900 text-white shadow-lg shadow-slate-900/10"
                  : "border-black/8 bg-white text-slate-900 hover:border-black/15 hover:bg-slate-50"
              )}
            >
              <button
                type="button"
                onClick={() => setActiveSession(session.id)}
                className="w-full text-left"
              >
                {isEditing ? (
                  <input
                    value={draftTitle}
                    onChange={(event) => setDraftTitle(event.target.value)}
                    onBlur={() => {
                      renameSession(session.id, draftTitle);
                      setEditingId(null);
                    }}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        renameSession(session.id, draftTitle);
                        setEditingId(null);
                      }

                      if (event.key === "Escape") {
                        setEditingId(null);
                      }
                    }}
                    autoFocus
                    className="w-full rounded-xl border border-white/20 bg-white/10 px-3 py-2 text-sm outline-none placeholder:text-slate-300"
                  />
                ) : (
                  <>
                    <p className="line-clamp-1 text-sm font-medium">{session.title}</p>
                    <p
                      className={cn(
                        "mt-1 line-clamp-2 text-xs leading-5",
                        isActive ? "text-slate-300" : "text-slate-500"
                      )}
                    >
                      {session.messages.at(-1)?.content || "还没有消息"}
                    </p>
                    <p className="mt-3 text-[11px] text-slate-400">
                      {formatTimestamp(session.updatedAt)}
                    </p>
                    <p className="mt-1 text-[11px] text-slate-400">
                      输入 {session.inputTokens} · 输出 {session.outputTokens}
                    </p>
                    <p className="mt-1 text-[11px] text-slate-400">Agent · {session.agentName}</p>
                  </>
                )}
              </button>

              {!isEditing ? (
                <div className="mt-3 flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setEditingId(session.id);
                      setDraftTitle(session.title);
                    }}
                    className={cn(
                      "rounded-full px-3 py-1 text-xs transition",
                      isActive
                        ? "bg-white/10 text-white hover:bg-white/15"
                        : "bg-slate-100 hover:bg-slate-200"
                    )}
                  >
                    重命名
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleDeleteSession(session.id)}
                    disabled={deletingSessionId === session.id}
                    className={cn(
                      "rounded-full px-3 py-1 text-xs transition",
                      isActive
                        ? "bg-red-500/20 text-red-100 hover:bg-red-500/30"
                        : "bg-red-50 text-red-600 hover:bg-red-100"
                    )}
                  >
                    {deletingSessionId === session.id ? "删除中..." : "删除"}
                  </button>
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </aside>
  );
}
