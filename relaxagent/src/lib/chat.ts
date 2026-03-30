import { ModelSettings } from "@/lib/settings";

export type MessageRole = "user" | "assistant" | "system";

export type ChatMessage = {
  id: string;
  role: MessageRole;
  content: string;
  createdAt: number;
};

export type ChatSession = {
  id: string;
  agentId: string;
  agentName: string;
  title: string;
  messages: ChatMessage[];
  inputTokens: number;
  outputTokens: number;
  createdAt: number;
  updatedAt: number;
};

export type SessionTokenUsage = {
  inputTokens: number;
  outputTokens: number;
};

export type ChatRequestPayload = {
  messages: Array<Pick<ChatMessage, "role" | "content">>;
  settings?: ModelSettings;
  sessionId?: string;
};

export type ChatStreamChunk =
  | {
      type: "text_delta";
      text: string;
    }
  | {
      type: "usage";
      inputTokens: number;
      outputTokens: number;
    };

export type SessionSnapshot = {
  id: string;
  agentId: string;
  title: string;
  messages: Array<Pick<ChatMessage, "role" | "content">>;
};

export function sessionSnapshotToChatSession(
  session: SessionSnapshot,
  index = 0,
  tokenUsage?: SessionTokenUsage,
  agentName = "未命名 Agent"
): ChatSession {
  const baseTimestamp = Date.now() - index * 60_000;

  return {
    id: session.id,
    agentId: session.agentId,
    agentName,
    title: session.title,
    messages: session.messages.map((message, messageIndex) => ({
      id: `${session.id}-${messageIndex}`,
      role: message.role,
      content: message.content,
      createdAt: baseTimestamp + messageIndex,
    })),
    inputTokens: tokenUsage?.inputTokens ?? 0,
    outputTokens: tokenUsage?.outputTokens ?? 0,
    createdAt: baseTimestamp,
    updatedAt: baseTimestamp + session.messages.length,
  };
}
