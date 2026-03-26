interface StepPromptProps {
  prompt: string
  theme?: 'dark' | 'light'
}

export default function StepPrompt({ prompt, theme = 'dark' }: StepPromptProps) {
  const isDark = theme === 'dark'
  return (
    <div className="h-full">
      <div className={`text-sm mb-4 ${isDark ? 'text-dark-500' : 'text-gray-500'}`}>
        组装后的完整 Prompt，将发送给大模型
      </div>
      <div className={`rounded-lg p-4 ${isDark ? 'bg-dark-900' : 'bg-gray-50 border border-gray-200'}`}>
        <div className={`flex items-center justify-between mb-3 ${isDark ? 'text-dark-500' : 'text-gray-500'}`}>
          <span className={`text-xs ${isDark ? 'text-blue-400' : 'text-blue-600'}`}>Prompt 内容</span>
          <span className={`text-xs ${isDark ? 'text-dark-600' : 'text-gray-400'}`}>{prompt.length} 字符</span>
        </div>
        <pre className={`whitespace-pre-wrap text-sm font-mono leading-relaxed max-h-96 overflow-auto ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          {prompt}
        </pre>
      </div>
    </div>
  )
}
