interface StepQueryProps {
  query: string
  theme?: 'dark' | 'light'
}

export default function StepQuery({ query, theme = 'dark' }: StepQueryProps) {
  const isDark = theme === 'dark'
  return (
    <div className="h-full flex flex-col items-center justify-center">
      <div className="text-center mb-8">
        <div className={`text-sm mb-2 ${isDark ? 'text-dark-500' : 'text-gray-500'}`}>用户提问</div>
        <h3 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>{query}</h3>
      </div>
      <div className={`rounded-lg p-6 w-full max-w-md ${isDark ? 'bg-dark-900' : 'bg-gray-50 border border-gray-200'}`}>
        <div className={`text-center text-sm mb-2 ${isDark ? 'text-dark-500' : 'text-gray-500'}`}>
          Query 将被向量化，用于后续相似度计算
        </div>
        <div className="text-center">
          <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg ${isDark ? 'bg-blue-600/20 text-blue-400' : 'bg-blue-50 text-blue-600'}`}>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            进入检索流程
          </div>
        </div>
      </div>
    </div>
  )
}
