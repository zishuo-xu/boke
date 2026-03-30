"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { ConnectionTestResponse, testModelConnection } from "@/lib/api";
import { ModelSettings } from "@/lib/settings";
import {
  defaultSettings,
  providerDefaults,
  useSettingsStore,
} from "@/store/use-settings-store";

export function SettingsForm() {
  const settings = useSettingsStore((state) => state.settings);
  const updateSettings = useSettingsStore((state) => state.updateSettings);
  const setProvider = useSettingsStore((state) => state.setProvider);
  const resetSettings = useSettingsStore((state) => state.resetSettings);
  const [draft, setDraft] = useState(settings);
  const [saved, setSaved] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    kind: "success" | "error";
    message: string;
    detail?: string;
  } | null>(null);

  useEffect(() => {
    setDraft(settings);
  }, [settings]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    updateSettings(draft);
    setSaved(true);
    window.setTimeout(() => setSaved(false), 1800);
  }

  async function handleTestConnection() {
    setTesting(true);
    setTestResult(null);

    try {
      const response = await testModelConnection(draft);
      const payload = (await response.json()) as ConnectionTestResponse;

      if (!response.ok || !payload.ok) {
        setTestResult({
          kind: "error",
          message:
            payload.elapsedMs != null
              ? `${payload.message}（${payload.elapsedMs} 毫秒）`
              : payload.message || "连接测试失败",
          detail: payload.detail,
        });
        return;
      }

      setTestResult({
        kind: "success",
        message:
          payload.elapsedMs != null
            ? `${payload.message}（${payload.elapsedMs} 毫秒）`
            : payload.message || "连接测试成功",
      });
    } catch (error) {
      setTestResult({
        kind: "error",
        message: error instanceof Error ? error.message : "连接测试失败",
      });
    } finally {
      setTesting(false);
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(148,163,184,0.18),_transparent_35%),linear-gradient(180deg,_#f8fafc_0%,_#eef2ff_100%)] px-4 py-10 sm:px-8">
      <div className="mx-auto max-w-3xl rounded-[36px] border border-black/10 bg-white/85 p-8 shadow-2xl shadow-slate-200/60 backdrop-blur">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">模型接入</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">
              模型设置
            </h1>
            <p className="mt-3 max-w-xl text-sm leading-7 text-slate-500">
              当前聊天已经切到 Agent 模式。这里主要用于调试模型连通和提供 API Key，Agent 自己决定角色提示词。
            </p>
          </div>
          <Link
            href="/"
            className="rounded-full border border-black/10 px-4 py-2 text-sm text-slate-700 transition hover:border-black/20 hover:bg-slate-100"
          >
            返回聊天
          </Link>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">服务提供商</span>
            <select
              value={draft.provider}
              onChange={(event) => {
                const provider = event.target.value as ModelSettings["provider"];
                setProvider(provider);
                setDraft((current) => ({
                  ...current,
                  provider,
                  baseURL: providerDefaults[provider].baseURL,
                  model: providerDefaults[provider].model,
                }));
              }}
              className="w-full rounded-2xl border border-black/10 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-slate-400 focus:bg-white"
            >
              <option value="openai-compatible">OpenAI 兼容协议</option>
              <option value="anthropic">Anthropic 原生协议</option>
            </select>
          </label>

          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">接口地址</span>
            <input
              value={draft.baseURL}
              onChange={(event) => setDraft({ ...draft, baseURL: event.target.value })}
              placeholder={defaultSettings.baseURL}
              className="w-full rounded-2xl border border-black/10 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-slate-400 focus:bg-white"
            />
          </label>

          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">API Key</span>
            <input
              value={draft.apiKey}
              onChange={(event) => setDraft({ ...draft, apiKey: event.target.value })}
              type="password"
              placeholder="sk-..."
              className="w-full rounded-2xl border border-black/10 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-slate-400 focus:bg-white"
            />
          </label>

          <div className="grid gap-6 sm:grid-cols-2">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">模型名称</span>
              <input
                value={draft.model}
                onChange={(event) => setDraft({ ...draft, model: event.target.value })}
                placeholder={defaultSettings.model}
                className="w-full rounded-2xl border border-black/10 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-slate-400 focus:bg-white"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">温度系数</span>
              <input
                value={draft.temperature}
                onChange={(event) =>
                setDraft({
                  ...draft,
                  temperature: Number(event.target.value),
                })
              }
              type="number"
                min="0"
                max="2"
                step="0.1"
                className="w-full rounded-2xl border border-black/10 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-slate-400 focus:bg-white"
              />
            </label>
          </div>

          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">系统提示词</span>
            <textarea
              value={draft.systemPrompt}
              onChange={(event) => setDraft({ ...draft, systemPrompt: event.target.value })}
              rows={5}
              className="w-full rounded-2xl border border-black/10 bg-slate-50 px-4 py-3 text-sm leading-7 outline-none transition focus:border-slate-400 focus:bg-white"
            />
          </label>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="submit"
              className="rounded-full bg-slate-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-700"
            >
              保存设置
            </button>
            <button
              type="button"
              onClick={() => void handleTestConnection()}
              disabled={testing}
              className="rounded-full border border-black/10 px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:border-black/20 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {testing ? "测试中..." : "测试连通"}
            </button>
            <button
              type="button"
              onClick={() => {
                resetSettings();
                setDraft({ ...defaultSettings });
                setTestResult(null);
              }}
              className="rounded-full border border-black/10 px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:border-black/20 hover:bg-slate-100"
            >
              重置默认值
            </button>
            {saved ? <span className="text-sm text-emerald-600">已保存</span> : null}
          </div>

          {testResult ? (
            <div
              className={
                testResult.kind === "success"
                  ? "rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700"
                  : "rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
              }
            >
              {testResult.message}
              {testResult.kind === "error" && testResult.detail ? (
                <p className="mt-2 break-words text-xs leading-6 opacity-80">
                  详细信息：{testResult.detail}
                </p>
              ) : null}
            </div>
          ) : null}
        </form>
      </div>
    </div>
  );
}
