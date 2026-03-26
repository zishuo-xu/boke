interface ControlBarProps {
  currentStep: number
  onNext: () => void
  onPrev: () => void
  onReset: () => void
  canGoNext: boolean
  canGoPrev: boolean
  theme?: 'dark' | 'light'
}

export default function ControlBar({
  currentStep,
  onNext,
  onPrev,
  onReset,
  canGoNext,
  canGoPrev,
  theme = 'dark'
}: ControlBarProps) {
  const isDark = theme === 'dark'

  return (
    <footer className={`border-t px-6 py-4 ${isDark ? 'bg-dark-800 border-dark-700' : 'bg-white border-gray-200'}`}>
      <div className="flex items-center justify-center gap-4">
        <button
          onClick={onReset}
          className={`px-6 py-2 rounded-lg transition-colors ${isDark ? 'bg-dark-700 text-gray-300 hover:bg-dark-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
        >
          重置
        </button>
        <button
          onClick={onPrev}
          disabled={!canGoPrev}
          className={`
            px-6 py-2 rounded-lg font-medium transition-all flex items-center gap-2
            ${canGoPrev
              ? isDark
                ? 'bg-dark-700 text-white hover:bg-dark-600'
                : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
              : isDark
                ? 'bg-dark-800 text-dark-600'
                : 'bg-gray-100 text-gray-400'
            }
          `}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          上一步
        </button>
        <div className={`px-4 py-2 rounded-lg text-center min-w-32 ${isDark ? 'bg-dark-900' : 'bg-gray-100'}`}>
          <span className="text-2xl font-bold text-blue-400">{currentStep}</span>
          <span className={`text-sm ${isDark ? 'text-dark-500' : 'text-gray-500'}`}> / 9</span>
        </div>
        <button
          onClick={onNext}
          disabled={!canGoNext}
          className={`
            px-6 py-2 rounded-lg font-medium transition-all flex items-center gap-2
            ${canGoNext
              ? 'bg-blue-600 text-white hover:bg-blue-500 shadow-lg shadow-blue-600/30'
              : isDark
                ? 'bg-dark-800 text-dark-600'
                : 'bg-gray-100 text-gray-400'
            }
          `}
        >
          下一步
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </footer>
  )
}
