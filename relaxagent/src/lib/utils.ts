import { ChatSession } from "@/lib/chat";

export function cn(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

export function formatTimestamp(timestamp: number) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(timestamp);
}

export function createId() {
  return crypto.randomUUID();
}

export function createSessionTitle(message: string) {
  const normalized = message.trim().replace(/\s+/g, " ");

  if (!normalized) {
    return "新会话";
  }

  return normalized.slice(0, 24);
}

export function sortSessionsByUpdatedAt(sessions: ChatSession[]) {
  return [...sessions].sort((a, b) => b.updatedAt - a.updatedAt);
}
