"use client";

import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import { Agent } from "@/lib/agent";

const AGENT_STORAGE_KEY = "relaxagent-agents";

type AgentStore = {
  agents: Agent[];
  selectedAgentId: string | null;
  replaceAgents: (agents: Agent[]) => void;
  setSelectedAgentId: (agentId: string) => void;
};

export const useAgentStore = create<AgentStore>()(
  persist(
    (set) => ({
      agents: [],
      selectedAgentId: null,
      replaceAgents: (agents) =>
        set((state) => {
          const selectedAgentId = agents.some((agent) => agent.id === state.selectedAgentId)
            ? state.selectedAgentId
            : agents[0]?.id ?? null;

          return {
            agents,
            selectedAgentId,
          };
        }),
      setSelectedAgentId: (agentId) => set({ selectedAgentId: agentId }),
    }),
    {
      name: AGENT_STORAGE_KEY,
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ selectedAgentId: state.selectedAgentId }),
    }
  )
);

export function useSelectedAgent() {
  return useAgentStore((state) =>
    state.agents.find((agent) => agent.id === state.selectedAgentId) ?? state.agents[0] ?? null
  );
}
