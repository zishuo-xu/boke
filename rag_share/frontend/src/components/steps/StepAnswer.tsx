interface StepAnswerProps {
  answer: string
  theme?: 'dark' | 'light'
}

export default function StepAnswer({ answer, theme = 'dark' }: StepAnswerProps) {
  const isDark = theme === 'dark'
  return (
    <div className="h-full flex flex-col">
      <div className={`text-sm mb-4 ${isDark ? 'text-dark-500' : 'text-gray-500'}`}>
        基于检索上下文生成的回答
      </div>
      <div className={`rounded-lg p-6 flex-1 ${isDark ? 'bg-gradient-to-br from-green-900/30 to-blue-900/30' : 'bg-gradient-to-br from-green-50 to-blue-50 border border-gray-200'}`}>
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <span className="text-sm font-medium text-green-400">答案生成完成</span>
        </div>
        <pre className={`whitespace-pre-wrap leading-relaxed ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          {answer}
        </pre>
      </div>
      <div className={`mt-4 text-center text-sm ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>
        以上是 RAG 流程的完整演示，感谢观看！
      </div>
    </div>
  )
}
