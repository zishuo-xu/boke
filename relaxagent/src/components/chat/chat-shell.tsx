"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef } from "react";
import { ChatInput } from "@/components/chat/chat-input";
import { MessageList } from "@/components/chat/message-list";
import { SessionSidebar } from "@/components/session/session-sidebar";
import { listAgents, listSessions, streamChat } from "@/lib/api";
import {
  ChatRequestPayload,
  ChatStreamChunk,
  SessionTokenUsage,
  sessionSnapshotToChatSession,
} from "@/lib/chat";
import { ensureSession, useActiveSession, useChatStore } from "@/store/use-chat-store";
import { useAgentStore } from "@/store/use-agent-store";
import { useSettingsStore } from "@/store/use-settings-store";

export function ChatShell() {
  const activeSession = useActiveSession();
  const settings = useSettingsStore((state) => state.settings);
  const addUserMessage = useChatStore((state) => state.addUserMessage);
  const appendAssistantChunk = useChatStore((state) => state.appendAssistantChunk);
  const finalizeAssistantMessage = useChatStore((state) => state.finalizeAssistantMessage);
  const applySessionUsage = useChatStore((state) => state.applySessionUsage);
  const replaceSessions = useChatStore((state) => state.replaceSessions);
  const setGenerating = useChatStore((state) => state.setGenerating);
  const isGenerating = useChatStore((state) => state.isGenerating);
  const error = useChatStore((state) => state.error);
  const setError = useChatStore((state) => state.setError);
  const replaceAgents = useAgentStore((state) => state.replaceAgents);
  const agents = useAgentStore((state) => state.agents);
  const abortRef = useRef<AbortController | null>(null);
  const hasLoadedSessionsRef = useRef(false);

  const statusText = useMemo(() => {
    if (!activeSession) {
      return "请先选择 Agent 并创建会话";
    }

    return settings.model
      ? `Agent · ${activeSession.agentName} · ${settings.model}`
      : `Agent · ${activeSession.agentName}`;
  }, [activeSession, settings.model]);

  useEffect(() => {
    if (hasLoadedSessionsRef.current) {
      return;
    }

    hasLoadedSessionsRef.current = true;

    void (async () => {
      try {
        const [agentList, sessions] = await Promise.all([listAgents(), listSessions()]);
        const agentNameMap = new Map(agentList.map((agent) => [agent.id, agent.name]));

        replaceAgents(agentList);
        replaceSessions(
          sessions.map((session, index) =>
            sessionSnapshotToChatSession(
              session,
              index,
              undefined,
              agentNameMap.get(session.agentId) ?? "未命名 Agent"
            )
          )
        );
      } catch (caughtError) {
        const message =
          caughtError instanceof Error ? caughtError.message : "加载会话列表失败。";
        setError(message);
      }
    })();
  }, [replaceAgents, replaceSessions, setError]);

  async function handleSend(content: string) {
    const sessionId = activeSession?.id ?? ensureSession();

    if (!sessionId || !activeSession) {
      setError("请先创建一个绑定 Agent 的会话。");
      return;
    }

    if (!settings.apiKey) {
      setError("请先在模型调试页填写 API Key。");
      return;
    }

    if (!settings.model) {
      setError("请先在模型调试页填写模型名称。");
      return;
    }

    const { assistantMessageId } = addUserMessage(sessionId, content);
    const controller = new AbortController();
    abortRef.current = controller;
    setGenerating(true);
    setError(null);

    try {
      const session = useChatStore.getState().sessions.find((item) => item.id === sessionId);

      const payload: ChatRequestPayload = {
        messages:
          session?.messages
            .filter((message) => message.role !== "assistant" || message.content)
            .map((message) => ({
              role: message.role,
              content: message.content,
            })) ?? [],
        settings,
        sessionId,
      };

      const response = await streamChat(payload, controller.signal);

      if (!response.ok || !response.body) {
        const message = await response.text();
        throw new Error(message || "请求失败，请稍后重试。");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullText = "";
      let buffer = "";
      let usage: SessionTokenUsage | null = null;

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          const trimmed = line.trim();

          if (!trimmed) {
            continue;
          }

          const chunk = JSON.parse(trimmed) as ChatStreamChunk;

          if (chunk.type === "text_delta") {
            fullText += chunk.text;
            appendAssistantChunk(sessionId, assistantMessageId, chunk.text);
          }

          if (chunk.type === "usage") {
            usage = {
              inputTokens: chunk.inputTokens,
              outputTokens: chunk.outputTokens,
            };
          }
        }
      }

      if (buffer.trim()) {
        const chunk = JSON.parse(buffer.trim()) as ChatStreamChunk;

        if (chunk.type === "text_delta") {
          fullText += chunk.text;
          appendAssistantChunk(sessionId, assistantMessageId, chunk.text);
        }

        if (chunk.type === "usage") {
          usage = {
            inputTokens: chunk.inputTokens,
            outputTokens: chunk.outputTokens,
          };
        }
      }

      finalizeAssistantMessage(sessionId, assistantMessageId, fullText);
      if (usage) {
        applySessionUsage(sessionId, usage);
      }
    } catch (caughtError) {
      const message =
        caughtError instanceof Error ? caughtError.message : "生成回复时发生未知错误。";

      if (controller.signal.aborted) {
        finalizeAssistantMessage(sessionId, assistantMessageId);
      } else {
        finalizeAssistantMessage(sessionId, assistantMessageId, "请求失败，请检查设置后重试。");
        setError(message);
      }
    } finally {
      setGenerating(false);
      abortRef.current = null;
    }
  }

  function handleStop() {
    abortRef.current?.abort();
    setGenerating(false);
  }

  return (
    <div className="grid h-screen overflow-hidden bg-[radial-gradient(circle_at_top_left,_rgba(125,211,252,0.25),_transparent_30%),radial-gradient(circle_at_bottom_right,_rgba(196,181,253,0.18),_transparent_28%),linear-gradient(180deg,_#f8fafc_0%,_#eef2ff_100%)] lg:grid-cols-[320px_minmax(0,1fr)]">
      <div className="min-h-0">
        <SessionSidebar />
      </div>

      <main className="flex min-h-0 flex-col overflow-hidden">
        <header className="border-b border-black/10 bg-white/70 px-4 py-4 backdrop-blur sm:px-8">
          <div className="mx-auto flex max-w-4xl flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Workspace</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">
                {activeSession?.title ?? "Simple LobeHub"}
              </h2>
              {activeSession ? (
                <p className="mt-2 text-sm text-slate-500">
                  输入 {activeSession.inputTokens} tokens · 输出 {activeSession.outputTokens} tokens ·
                  总计 {activeSession.inputTokens + activeSession.outputTokens} tokens
                </p>
              ) : null}
            </div>
            <div className="flex items-center gap-3">
              <span className="rounded-full border border-black/10 bg-white px-4 py-2 text-sm text-slate-600">
                {statusText}
              </span>
              <Link
                href="/settings"
                className="rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700"
              >
                模型调试
              </Link>
            </div>
          </div>
        </header>

        {error ? (
          <div className="px-4 pt-4 sm:px-8">
            <div className="mx-auto max-w-4xl rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          </div>
        ) : null}

        <MessageList session={activeSession} />
        <ChatInput
          disabled={!activeSession || agents.length === 0 || !settings.apiKey}
          isGenerating={isGenerating}
          onSend={handleSend}
          onStop={handleStop}
        />
      </main>
    </div>
  );
}
