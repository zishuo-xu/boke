import { STEPS } from '../App'

interface StepNavigationProps {
  currentStep: number
  onJumpToStep: (step: number) => void
  theme?: 'dark' | 'light'
}

export default function StepNavigation({ currentStep, onJumpToStep, theme = 'dark' }: StepNavigationProps) {
  const isDark = theme === 'dark'

  return (
    <nav className={`border-b px-6 py-3 ${isDark ? 'bg-dark-800 border-dark-700' : 'bg-white border-gray-200'}`}>
      <div className="flex items-center gap-2 overflow-x-auto">
        {STEPS.map((step, index) => (
          <div key={step.id} className="flex items-center">
            <button
              onClick={() => onJumpToStep(step.id)}
              className={`
                px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap
                ${currentStep === step.id
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                  : currentStep > step.id
                    ? isDark
                      ? 'bg-dark-700 text-blue-400 hover:bg-dark-600'
                      : 'bg-gray-200 text-blue-600 hover:bg-gray-300'
                    : isDark
                      ? 'bg-dark-700/50 text-dark-500 hover:bg-dark-700'
                      : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
                }
              `}
            >
              {step.id}. {step.name}
            </button>
            {index < STEPS.length - 1 && (
              <svg
                className={`w-4 h-4 mx-1 ${currentStep > step.id ? 'text-blue-500' : isDark ? 'text-dark-600' : 'text-gray-300'}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            )}
          </div>
        ))}
      </div>
    </nav>
  )
}
