export type Agent = {
  id: string;
  name: string;
  description: string;
  provider: "openai-compatible" | "anthropic";
  model: string;
  systemPrompt: string;
};
