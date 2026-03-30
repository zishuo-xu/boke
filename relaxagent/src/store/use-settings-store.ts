"use client";

import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import { ModelSettings } from "@/lib/settings";
import { SETTINGS_STORAGE_KEY } from "@/lib/storage";

const defaultSettings: ModelSettings = {
  provider: "openai-compatible",
  baseURL: "https://api.openai.com/v1",
  apiKey: "",
  model: "gpt-4o-mini",
  temperature: 0.7,
  systemPrompt: "You are a helpful AI assistant.",
};

const providerDefaults: Record<ModelSettings["provider"], Pick<ModelSettings, "baseURL" | "model">> =
  {
    "openai-compatible": {
      baseURL: "https://api.openai.com/v1",
      model: "gpt-4o-mini",
    },
    anthropic: {
      baseURL: "https://api.anthropic.com/v1",
      model: "claude-sonnet-4-20250514",
    },
  };

type SettingsStore = {
  settings: ModelSettings;
  updateSettings: (next: Partial<ModelSettings>) => void;
  setProvider: (provider: ModelSettings["provider"]) => void;
  resetSettings: () => void;
};

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set) => ({
      settings: defaultSettings,
      updateSettings: (next) =>
        set((state) => ({
          settings: {
            ...state.settings,
            ...next,
          },
        })),
      setProvider: (provider) =>
        set((state) => ({
          settings: {
            ...state.settings,
            provider,
            baseURL: providerDefaults[provider].baseURL,
            model: providerDefaults[provider].model,
          },
        })),
      resetSettings: () => set({ settings: defaultSettings }),
    }),
    {
      name: SETTINGS_STORAGE_KEY,
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ settings: state.settings }),
    }
  )
);

export { defaultSettings, providerDefaults };
