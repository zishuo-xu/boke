"use client";

import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import { ChatMessage, ChatSession, SessionTokenUsage } from "@/lib/chat";
import { CHAT_STORAGE_KEY } from "@/lib/storage";
import { createId, createSessionTitle, sortSessionsByUpdatedAt } from "@/lib/utils";

type ChatStore = {
  sessions: ChatSession[];
  activeSessionId: string | null;
  isGenerating: boolean;
  error: string | null;
  createSession: (agentId: string, agentName: string) => string;
  insertSession: (session: ChatSession) => void;
  replaceSessions: (sessions: ChatSession[]) => void;
  setActiveSession: (sessionId: string) => void;
  deleteSession: (sessionId: string) => void;
  renameSession: (sessionId: string, title: string) => void;
  addUserMessage: (
    sessionId: string,
    content: string
  ) => { userMessageId: string; assistantMessageId: string };
  appendAssistantChunk: (sessionId: string, messageId: string, chunk: string) => void;
  finalizeAssistantMessage: (sessionId: string, messageId: string, content?: string) => void;
  applySessionUsage: (sessionId: string, usage: SessionTokenUsage) => void;
  setGenerating: (isGenerating: boolean) => void;
  setError: (error: string | null) => void;
};

function buildEmptySession(): ChatSession {
  const now = Date.now();

  return {
    id: createId(),
    agentId: "",
    agentName: "未命名 Agent",
    title: "新会话",
    messages: [],
    inputTokens: 0,
    outputTokens: 0,
    createdAt: now,
    updatedAt: now,
  };
}

function updateSessions(
  sessions: ChatSession[],
  sessionId: string,
  updater: (session: ChatSession) => ChatSession
) {
  return sortSessionsByUpdatedAt(
    sessions.map((session) => (session.id === sessionId ? updater(session) : session))
  );
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set) => ({
      sessions: [],
      activeSessionId: null,
      isGenerating: false,
      error: null,
      createSession: (agentId, agentName) => {
        const nextSession = buildEmptySession();
        nextSession.agentId = agentId;
        nextSession.agentName = agentName;

        set((state) => ({
          sessions: [nextSession, ...state.sessions],
          activeSessionId: nextSession.id,
          error: null,
        }));

        return nextSession.id;
      },
      insertSession: (session) =>
        set((state) => {
          const existingIndex = state.sessions.findIndex((item) => item.id === session.id);
          const nextSessions =
            existingIndex >= 0
              ? state.sessions.map((item) => (item.id === session.id ? session : item))
              : [session, ...state.sessions];

          return {
            sessions: sortSessionsByUpdatedAt(nextSessions),
            activeSessionId: session.id,
            error: null,
          };
        }),
      replaceSessions: (sessions) =>
        set((state) => {
          const normalized = sortSessionsByUpdatedAt(sessions);
          const activeSessionId = normalized.some((session) => session.id === state.activeSessionId)
            ? state.activeSessionId
            : normalized[0]?.id ?? null;

          return {
            sessions: normalized,
            activeSessionId,
          };
        }),
      setActiveSession: (sessionId) => set({ activeSessionId: sessionId }),
      deleteSession: (sessionId) =>
        set((state) => {
          const sessions = state.sessions.filter((session) => session.id !== sessionId);
          const activeSessionId =
            state.activeSessionId === sessionId ? sessions[0]?.id ?? null : state.activeSessionId;

          return { sessions, activeSessionId };
        }),
      renameSession: (sessionId, title) =>
        set((state) => ({
          sessions: updateSessions(state.sessions, sessionId, (session) => ({
            ...session,
            title: title.trim() || session.title,
            updatedAt: Date.now(),
          })),
        })),
      addUserMessage: (sessionId, content) => {
        const now = Date.now();
        const trimmed = content.trim();
        const userMessageId = createId();
        const assistantMessageId = createId();

        set((state) => ({
          sessions: updateSessions(state.sessions, sessionId, (session) => {
            const userMessage: ChatMessage = {
              id: userMessageId,
              role: "user",
              content: trimmed,
              createdAt: now,
            };
            const assistantMessage: ChatMessage = {
              id: assistantMessageId,
              role: "assistant",
              content: "",
              createdAt: now + 1,
            };

            return {
              ...session,
              title:
                session.messages.length === 0 ? createSessionTitle(trimmed) : session.title,
              messages: [...session.messages, userMessage, assistantMessage],
              updatedAt: now,
            };
          }),
          error: null,
        }));

        return { userMessageId, assistantMessageId };
      },
      appendAssistantChunk: (sessionId, messageId, chunk) =>
        set((state) => ({
          sessions: updateSessions(state.sessions, sessionId, (session) => ({
            ...session,
            messages: session.messages.map((message) =>
              message.id === messageId
                ? {
                    ...message,
                    content: message.content + chunk,
                  }
                : message
            ),
            updatedAt: Date.now(),
          })),
        })),
      finalizeAssistantMessage: (sessionId, messageId, content) =>
        set((state) => ({
          sessions: updateSessions(state.sessions, sessionId, (session) => ({
            ...session,
            messages: session.messages.map((message) =>
              message.id === messageId
                ? {
                    ...message,
                    content: content ?? (message.content || "已停止生成。"),
                  }
                : message
            ),
            updatedAt: Date.now(),
          })),
        })),
      applySessionUsage: (sessionId, usage) =>
        set((state) => ({
          sessions: updateSessions(state.sessions, sessionId, (session) => ({
            ...session,
            inputTokens: session.inputTokens + usage.inputTokens,
            outputTokens: session.outputTokens + usage.outputTokens,
            updatedAt: Date.now(),
          })),
        })),
      setGenerating: (isGenerating) => set({ isGenerating }),
      setError: (error) => set({ error }),
    }),
    {
      name: CHAT_STORAGE_KEY,
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        sessions: state.sessions,
        activeSessionId: state.activeSessionId,
      }),
      onRehydrateStorage: () => (state) => {
        if (!state) {
          return;
        }

        state.sessions = state.sessions.map((session) => ({
          ...session,
          agentId: session.agentId ?? "",
          agentName: session.agentName ?? "未命名 Agent",
          inputTokens: session.inputTokens ?? 0,
          outputTokens: session.outputTokens ?? 0,
        }));

        const activeSessionExists = state.sessions.some(
          (session) => session.id === state.activeSessionId
        );

        if (!activeSessionExists) {
          state.activeSessionId = state.sessions[0]?.id ?? null;
        }
      },
    }
  )
);

export function useActiveSession() {
  return useChatStore((state) =>
    state.sessions.find((session) => session.id === state.activeSessionId) ?? null
  );
}

export function ensureSession() {
  const { activeSessionId, sessions } = useChatStore.getState();

  if (activeSessionId && sessions.some((session) => session.id === activeSessionId)) {
    return activeSessionId;
  }

  return null;
}
