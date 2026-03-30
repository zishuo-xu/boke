export type ProviderType = "openai-compatible" | "anthropic";

export type ModelSettings = {
  provider: ProviderType;
  baseURL: string;
  apiKey: string;
  model: string;
  temperature: number;
  systemPrompt: string;
};
