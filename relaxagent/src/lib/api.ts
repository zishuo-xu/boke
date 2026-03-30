import { Agent } from "@/lib/agent";
import { ChatRequestPayload, MessageRole } from "@/lib/chat";
import { ModelSettings } from "@/lib/settings";

const DEFAULT_BACKEND_BASE_URL = "http://127.0.0.1:8000/api/v1";

export function getBackendBaseUrl() {
  return (
    process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ??
    DEFAULT_BACKEND_BASE_URL
  );
}

export async function streamChat(
  payload: ChatRequestPayload,
  signal?: AbortSignal
) {
  return fetch(`${getBackendBaseUrl()}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    signal,
  });
}

export async function testModelConnection(settings: ModelSettings) {
  return fetch(`${getBackendBaseUrl()}/providers/test`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(settings),
  });
}

export type BackendSession = {
  id: string;
  agentId: string;
  title: string;
  messages: Array<{
    role: MessageRole;
    content: string;
  }>;
};

export async function listSessions() {
  const response = await fetch(`${getBackendBaseUrl()}/sessions`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error((await response.text()) || "获取会话列表失败。");
  }

  return (await response.json()) as BackendSession[];
}

export async function listAgents() {
  const response = await fetch(`${getBackendBaseUrl()}/agents`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error((await response.text()) || "获取 Agent 列表失败。");
  }

  return (await response.json()) as Agent[];
}

export async function getSession(sessionId: string) {
  const response = await fetch(`${getBackendBaseUrl()}/sessions/${sessionId}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error((await response.text()) || "获取会话详情失败。");
  }

  return (await response.json()) as BackendSession;
}

export async function createRemoteSession(sessionId: string, agentId: string, title?: string) {
  const response = await fetch(`${getBackendBaseUrl()}/sessions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      sessionId,
      agentId,
      title,
    }),
  });

  if (!response.ok) {
    throw new Error((await response.text()) || "创建会话失败。");
  }

  return (await response.json()) as BackendSession;
}

export async function deleteRemoteSession(sessionId: string) {
  const response = await fetch(`${getBackendBaseUrl()}/sessions/${sessionId}`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error((await response.text()) || "删除会话失败。");
  }
}

export type ConnectionTestResponse = {
  ok: boolean;
  code:
    | "ok"
    | "validation_error"
    | "auth_error"
    | "model_error"
    | "endpoint_error"
    | "rate_limit"
    | "network_error"
    | "provider_error";
  message: string;
  detail?: string;
  elapsedMs?: number;
};
