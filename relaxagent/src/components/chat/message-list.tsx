"use client";

import { useEffect, useRef } from "react";
import { ChatMessage } from "@/components/chat/chat-message";
import { ChatSession } from "@/lib/chat";

type MessageListProps = {
  session: ChatSession | null;
};

export function MessageList({ session }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [session?.messages]);

  if (!session) {
    return (
      <div className="flex min-h-0 flex-1 items-center justify-center px-6">
        <div className="max-w-lg rounded-[32px] border border-dashed border-black/10 bg-white/80 px-8 py-10 text-center shadow-sm">
          <p className="text-xs uppercase tracking-[0.34em] text-slate-400">RelaxAgent</p>
          <h2 className="mt-4 text-3xl font-semibold tracking-tight text-slate-900">
            先创建一个会话
          </h2>
          <p className="mt-4 text-sm leading-7 text-slate-500">
            这是一个面向个人使用的简单版 LobeHub。先在左侧新建会话，再在底部输入问题即可开始。
          </p>
        </div>
      </div>
    );
  }

  if (session.messages.length === 0) {
    return (
      <div className="flex min-h-0 flex-1 items-center justify-center px-6">
        <div className="max-w-xl rounded-[32px] border border-black/10 bg-white/80 px-8 py-10 shadow-sm">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Session Ready</p>
          <h2 className="mt-4 text-3xl font-semibold tracking-tight text-slate-900">
            {session.title}
          </h2>
          <p className="mt-4 text-sm leading-7 text-slate-500">
            你已经有一个空会话了。底部支持多行输入，发送后会自动保存聊天记录。
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-0 flex-1 overflow-y-auto px-4 py-6 sm:px-8">
      <div className="mx-auto flex max-w-4xl flex-col gap-4">
        {session.messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
