import { useState, useReducer, useCallback, useEffect } from 'react'
import axios from 'axios'
import StepNavigation from './components/StepNavigation'
import InputPanel from './components/InputPanel'
import MainDemo from './components/MainDemo'
import ExplanationPanel from './components/ExplanationPanel'
import ControlBar from './components/ControlBar'

export interface Chunk {
  id: string
  text: string
  length: number
}

export interface RetrievalResult {
  chunk_id: string
  similarity: number
}

export interface RerankedResult {
  chunk_id: string
  original_rank: number
  new_rank: number
  similarity: number
}

export interface RagProcessResult {
  preprocessed_text: string
  chunks: Chunk[]
  vectors: number[][]
  query_vector: number[]
  retrieval_results: RetrievalResult[]
  reranked_results: RerankedResult[] | null
  prompt: string
  answer: string
}

export interface ProcessRequest {
  text: string
  query: string
  chunk_size: number
  overlap: number
  top_k: number
  use_rerank: boolean
  chunking_strategy: string
}

export const STEPS = [
  { id: 1, name: '原始文本', description: '展示输入的原始文档' },
  { id: 2, name: '预处理', description: '文本清洗和标准化' },
  { id: 3, name: '切片', description: '将文本切分成 chunks' },
  { id: 4, name: '向量化', description: '将 chunks 转为向量' },
  { id: 5, name: '用户提问', description: '展示 Query 输入' },
  { id: 6, name: '相似度检索', description: '计算相似度并召回' },
  { id: 7, name: '重排', description: '对召回结果重排序' },
  { id: 8, name: 'Prompt 组装', description: '组装最终 Prompt' },
  { id: 9, name: '答案生成', description: '展示最终回答' }
]

type AppAction =
  | { type: 'NEXT_STEP' }
  | { type: 'PREV_STEP' }
  | { type: 'GO_TO_STEP'; payload: number }
  | { type: 'RESET' }
  | { type: 'SET_PROCESSING'; payload: boolean }
  | { type: 'SET_RESULT'; payload: RagProcessResult }

interface AppState {
  currentStep: number
  isProcessing: boolean
  result: RagProcessResult | null
}

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'NEXT_STEP':
      return { ...state, currentStep: Math.min(state.currentStep + 1, 9) }
    case 'PREV_STEP':
      return { ...state, currentStep: Math.max(state.currentStep - 1, 1) }
    case 'GO_TO_STEP':
      return { ...state, currentStep: action.payload }
    case 'RESET':
      return { currentStep: 1, isProcessing: false, result: null }
    case 'SET_PROCESSING':
      return { ...state, isProcessing: action.payload }
    case 'SET_RESULT':
      return { ...state, result: action.payload, isProcessing: false }
    default:
      return state
  }
}

const DEFAULT_TEXT = `人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，致力于开发能够执行通常需要人类智能的任务的系统。这包括视觉感知、语音识别、决策制定和语言翻译等。

机器学习是人工智能的一个子集，它使系统能够从数据中学习并改进性能，而无需明确编程。深度学习则是机器学习的一个分支，使用多层神经网络来分析各种因素的数据。

大型语言模型（LLM）是深度学习在自然语言处理领域的应用，能够理解和生成人类语言。检索增强生成（RAG）技术结合了检索系统和生成模型，提高了AI系统的准确性和可靠性。`

const DEFAULT_QUERY = '什么是RAG技术？'

const STORAGE_KEY = 'rag_demo_input'

function App() {
  // 从 localStorage 加载保存的输入
  const loadSavedInput = (): ProcessRequest => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        return JSON.parse(saved)
      }
    } catch (e) {
      console.error('Failed to load saved input:', e)
    }
    return {
      text: DEFAULT_TEXT,
      query: DEFAULT_QUERY,
      chunk_size: 50,
      overlap: 10,
      top_k: 3,
      use_rerank: true,
      chunking_strategy: 'by_chars'
    }
  }

  const [state, dispatch] = useReducer(appReducer, {
    currentStep: 1,
    isProcessing: false,
    result: null
  })

  const [inputData, setInputData] = useState<ProcessRequest>(loadSavedInput)
  const [editedChunks, setEditedChunks] = useState<Chunk[] | null>(null)
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    const saved = localStorage.getItem('rag_demo_theme')
    return (saved as 'dark' | 'light') || 'dark'
  })

  // 主题切换
  const toggleTheme = () => {
    setTheme(prev => {
      const next = prev === 'dark' ? 'light' : 'dark'
      localStorage.setItem('rag_demo_theme', next)
      return next
    })
  }

  // 保存输入到 localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(inputData))
    } catch (e) {
      console.error('Failed to save input:', e)
    }
  }, [inputData])

  // 键盘快捷键
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // 忽略输入框内的按键
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return
      }

      switch (e.key) {
        case 'ArrowRight':
        case 'ArrowDown':
          if (state.currentStep < 9 && state.result) {
            dispatch({ type: 'NEXT_STEP' })
          }
          break
        case 'ArrowLeft':
        case 'ArrowUp':
          if (state.currentStep > 1) {
            dispatch({ type: 'PREV_STEP' })
          }
          break
        case 'r':
        case 'R':
          if (!e.ctrlKey && !e.metaKey) {
            handleReset()
          }
          break
        case '?':
          // 显示快捷键提示
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [state.currentStep, state.result])

  const handleProcess = useCallback(async () => {
    dispatch({ type: 'SET_PROCESSING', payload: true })
    setEditedChunks(null)
    try {
      const response = await axios.post<{ preprocessed_text: string; chunks: Chunk[]; vectors: number[][]; query_vector: number[]; retrieval_results: RetrievalResult[]; reranked_results: RerankedResult[] | null; prompt: string; answer: string }>('/api/rag/process', inputData)
      dispatch({ type: 'SET_RESULT', payload: response.data })
      dispatch({ type: 'GO_TO_STEP', payload: 2 })
    } catch (error) {
      console.error('API Error:', error)
      dispatch({ type: 'SET_PROCESSING', payload: false })
      alert('请求失败，请检查后端服务是否启动')
    }
  }, [inputData])

  const handleReset = () => {
    dispatch({ type: 'RESET' })
    setEditedChunks(null)
  }

  const handleNext = () => dispatch({ type: 'NEXT_STEP' })
  const handlePrev = () => dispatch({ type: 'PREV_STEP' })
  const handleJumpToStep = (step: number) => dispatch({ type: 'GO_TO_STEP', payload: step })

  const isDark = theme === 'dark'

  return (
    <div className={`min-h-screen flex flex-col ${isDark ? 'bg-dark-900 text-gray-100' : 'bg-gray-50 text-gray-900'}`}>
      {/* Header */}
      <header className={`border-b px-6 py-4 ${isDark ? 'bg-dark-800 border-dark-700' : 'bg-white border-gray-200'}`}>
        <div className="flex items-center justify-between">
          <h1 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>RAG 可视化演示</h1>
          <div className="flex items-center gap-4">
            <div className={`text-sm ${isDark ? 'text-dark-600' : 'text-gray-400'}`}>
              <span className="hidden sm:inline">快捷键: </span>
              <kbd className={`px-1.5 py-0.5 rounded text-xs ${isDark ? 'bg-dark-700' : 'bg-gray-200'}`}>←</kbd>
              <kbd className={`px-1.5 py-0.5 rounded text-xs ${isDark ? 'bg-dark-700' : 'bg-gray-200'}`}>→</kbd>
              <span className="ml-1">上一步/下一步</span>
              <kbd className={`ml-2 px-1.5 py-0.5 rounded text-xs ${isDark ? 'bg-dark-700' : 'bg-gray-200'}`}>R</kbd>
              <span className="ml-1">重置</span>
            </div>
            <button
              onClick={toggleTheme}
              className={`p-2 rounded-lg transition-colors ${isDark ? 'bg-dark-700 hover:bg-dark-600 text-yellow-400' : 'bg-gray-200 hover:bg-gray-300 text-gray-700'}`}
              title={isDark ? '切换到明亮模式' : '切换到暗黑模式'}
            >
              {isDark ? (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" strokeWidth="2" stroke="currentColor" fill="none"/>
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Step Navigation */}
      <StepNavigation
        currentStep={state.currentStep}
        onJumpToStep={handleJumpToStep}
        theme={theme}
      />

      {/* Main Content */}
      <main className="flex-1 flex gap-4 p-4 overflow-hidden">
        {/* Left Panel - Input */}
        <aside className="w-80 flex-shrink-0">
          <InputPanel
            inputData={inputData}
            setInputData={setInputData}
            onProcess={handleProcess}
            isProcessing={state.isProcessing}
            hasResult={!!state.result}
            theme={theme}
          />
        </aside>

        {/* Center - Main Demo */}
        <section className="flex-1 min-w-0">
          <MainDemo
            currentStep={state.currentStep}
            inputData={inputData}
            result={state.result}
            editedChunks={editedChunks}
            setEditedChunks={setEditedChunks}
            theme={theme}
          />
        </section>

        {/* Right Panel - Explanation */}
        <aside className="w-80 flex-shrink-0">
          <ExplanationPanel
            currentStep={state.currentStep}
            inputData={inputData}
            result={state.result}
            theme={theme}
          />
        </aside>
      </main>

      {/* Control Bar */}
      <ControlBar
        currentStep={state.currentStep}
        onNext={handleNext}
        onPrev={handlePrev}
        onReset={handleReset}
        canGoNext={state.currentStep < 9 && !!state.result}
        canGoPrev={state.currentStep > 1}
        theme={theme}
      />
    </div>
  )
}

export default App
