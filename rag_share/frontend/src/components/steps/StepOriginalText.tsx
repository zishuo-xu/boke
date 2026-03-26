interface StepOriginalTextProps {
  text: string
  theme?: 'dark' | 'light'
}

export default function StepOriginalText({ text, theme = 'dark' }: StepOriginalTextProps) {
  const isDark = theme === 'dark'
  return (
    <div className="h-full">
      <div className={`rounded-lg p-4 h-full ${isDark ? 'bg-dark-900' : 'bg-gray-50 border border-gray-200'}`}>
        <div className={`flex items-center justify-between mb-3 ${isDark ? 'text-dark-500' : 'text-gray-500'}`}>
          <span>原始文档内容</span>
          <span className={`text-xs ${isDark ? 'text-dark-600' : 'text-gray-400'}`}>{text.length} 字符</span>
        </div>
        <pre className={`whitespace-pre-wrap text-sm leading-relaxed font-sans ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          {text}
        </pre>
      </div>
    </div>
  )
}
