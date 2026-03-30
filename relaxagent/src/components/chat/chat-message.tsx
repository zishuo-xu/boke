"use client";

import ReactMarkdown from "react-markdown";
import { ChatMessage as ChatMessageType } from "@/lib/chat";
import { cn, formatTimestamp } from "@/lib/utils";

type ChatMessageProps = {
  message: ChatMessageType;
};

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <article className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-3xl rounded-[28px] px-5 py-4 shadow-sm",
          isUser
            ? "bg-slate-900 text-white"
            : "border border-black/8 bg-white text-slate-900"
        )}
      >
        <div className="mb-3 flex items-center gap-2 text-xs uppercase tracking-[0.2em]">
          <span className={cn(isUser ? "text-slate-300" : "text-slate-400")}>
            {isUser ? "You" : "Assistant"}
          </span>
          <span className={cn(isUser ? "text-slate-500" : "text-slate-300")}>•</span>
          <span className={cn(isUser ? "text-slate-400" : "text-slate-400")}>
            {formatTimestamp(message.createdAt)}
          </span>
        </div>

        {message.content ? (
          <div
            className={cn(
              "prose prose-sm max-w-none whitespace-pre-wrap break-words",
              isUser ? "prose-invert" : "prose-slate"
            )}
          >
            <ReactMarkdown
              components={{
                code(props) {
                  return (
                    <code className="rounded bg-black/8 px-1.5 py-0.5 text-[0.95em]">
                      {props.children}
                    </code>
                  );
                },
                pre(props) {
                  return (
                    <pre className="overflow-x-auto rounded-2xl bg-slate-950/95 p-4 text-slate-100">
                      {props.children}
                    </pre>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        ) : (
          <div className="flex items-center gap-1 py-2">
            <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400" />
            <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400 [animation-delay:120ms]" />
            <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400 [animation-delay:240ms]" />
          </div>
        )}
      </div>
    </article>
  );
}
