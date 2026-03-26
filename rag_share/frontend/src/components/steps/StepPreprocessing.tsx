interface StepPreprocessingProps {
  original: string
  preprocessed: string
  theme?: 'dark' | 'light'
}

export default function StepPreprocessing({ original, preprocessed, theme = 'dark' }: StepPreprocessingProps) {
  const isDark = theme === 'dark'
  return (
    <div className="h-full flex gap-4">
      {/* Before */}
      <div className={`flex-1 rounded-lg p-4 ${isDark ? 'bg-dark-900' : 'bg-gray-50 border border-gray-200'}`}>
        <div className={`flex items-center justify-between mb-3 ${isDark ? 'text-dark-500' : 'text-gray-500'}`}>
          <span className="text-sm text-red-400">处理前</span>
          <span className={`text-xs ${isDark ? 'text-dark-600' : 'text-gray-400'}`}>{original.length} 字符</span>
        </div>
        <pre className={`whitespace-pre-wrap text-sm leading-relaxed font-sans h-48 overflow-auto ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          {original}
        </pre>
      </div>

      {/* Arrow */}
      <div className="flex items-center">
        <div className="w-12 h-12 bg-blue-600/20 rounded-full flex items-center justify-center">
          <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </div>
      </div>

      {/* After */}
      <div className={`flex-1 rounded-lg p-4 ${isDark ? 'bg-dark-900' : 'bg-gray-50 border border-gray-200'}`}>
        <div className={`flex items-center justify-between mb-3 ${isDark ? 'text-dark-500' : 'text-gray-500'}`}>
          <span className="text-sm text-green-400">处理后</span>
          <span className={`text-xs ${isDark ? 'text-dark-600' : 'text-gray-400'}`}>{preprocessed.length} 字符</span>
        </div>
        <pre className={`whitespace-pre-wrap text-sm leading-relaxed font-sans h-48 overflow-auto ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          {preprocessed}
        </pre>
      </div>
    </div>
  )
}
