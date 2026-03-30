"use client";

import { FormEvent, KeyboardEvent, useState } from "react";
import { cn } from "@/lib/utils";

type ChatInputProps = {
  disabled?: boolean;
  isGenerating: boolean;
  onSend: (message: string) => Promise<void>;
  onStop: () => void;
};

export function ChatInput({
  disabled = false,
  isGenerating,
  onSend,
  onStop,
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    const trimmed = value.trim();

    if (!trimmed || disabled || isSubmitting || isGenerating) {
      return;
    }

    setIsSubmitting(true);
    setValue("");

    try {
      await onSend(trimmed);
    } catch (error) {
      setValue(trimmed);
      throw error;
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void handleSubmit();
    }
  }

  return (
    <form
      onSubmit={(event) => void handleSubmit(event)}
      className="border-t border-black/10 bg-white/90 px-4 py-4 backdrop-blur sm:px-8"
    >
      <div className="mx-auto max-w-4xl rounded-[30px] border border-black/10 bg-white p-3 shadow-lg shadow-slate-200/40">
        <textarea
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || isGenerating}
          placeholder="输入你的问题，Shift + Enter 换行"
          rows={4}
          className="min-h-28 w-full resize-none rounded-2xl border-0 bg-transparent px-3 py-3 text-sm leading-7 text-slate-900 outline-none placeholder:text-slate-400"
        />
        <div className="mt-3 flex items-center justify-between gap-3">
          <p className="text-xs leading-5 text-slate-400">
            当前版本先聚焦核心聊天体验，历史消息会自动保存在本地。
          </p>
          <div className="flex items-center gap-2">
            {isGenerating ? (
              <button
                type="button"
                onClick={onStop}
                className="rounded-full border border-red-200 bg-red-50 px-4 py-2 text-sm font-medium text-red-600 transition hover:bg-red-100"
              >
                停止
              </button>
            ) : null}
            <button
              type="submit"
              disabled={disabled || !value.trim() || isSubmitting || isGenerating}
              className={cn(
                "rounded-full px-5 py-2.5 text-sm font-medium transition",
                disabled || !value.trim() || isSubmitting || isGenerating
                  ? "cursor-not-allowed bg-slate-200 text-slate-400"
                  : "bg-slate-900 text-white hover:bg-slate-700"
              )}
            >
              发送
            </button>
          </div>
        </div>
      </div>
    </form>
  );
}
