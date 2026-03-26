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

const DEFAULT_TEXT = `智能客服系统用户手册

第一章：系统概述

智能客服系统是一套基于人工智能技术的在线客户服务解决方案，旨在为企业提供高效、准确、7×24小时在线的客户支持服务。本系统整合了自然语言处理、机器学习、知识图谱等多项先进技术，能够理解用户意图并提供精准的答案。

系统主要功能包括：智能问答自动回复、多轮对话管理、意图识别、情感分析、问题转人工、知识库管理、数据统计分析等。通过这些功能，企业可以显著降低客服成本，同时提升客户满意度和服务效率。

第二章：系统架构

本系统采用微服务架构设计，主要包含以下核心模块：

自然语言理解模块负责对用户输入进行分词、词性标注、命名实体识别等预处理操作，提取出文本中的关键信息和语义特征。该模块基于深度学习模型构建，经过大量语料训练，能够准确理解各种表达方式的用户query。

对话管理模块控制对话流程，维护对话状态，支持多轮对话场景。当用户提出复杂问题时，系统能够通过多轮交互逐步澄清用户需求，最终给出准确答案。该模块还负责对话策略的选择，决定何时调用知识库检索、何时转人工服务。

知识库检索模块是系统的核心组件，基于RAG（检索增强生成）架构构建。当用户提出问题时，系统首先在知识库中检索相关内容，然后结合检索结果生成答案。知识库支持多种格式的内容导入，包括FAQ文档、产品手册、操作指南等。

答案生成模块负责将检索到的内容和用户问题组合成完整的回答。系统使用大语言模型进行答案生成，能够生成流畅、自然的回复，同时确保答案基于知识库中的真实内容。

第三章：知识库管理

知识库是智能客服系统的基础，高质量的知识库是系统良好运行的前提。知识库管理功能包括知识的创建、编辑、审核、发布全流程管理。

知识条目由问题和答案组成，支持富文本格式。管理员可以为知识条目设置分类标签、关键词、相似问法等属性，提高检索召回率。系统还支持知识条目的批量导入和导出，方便与企业现有知识库对接。

知识库的维护需要持续进行。管理员应定期审查知识库内容，更新老旧信息，补充新常见问题。系统提供数据分析功能，可以统计各知识条目的访问频率、满意度评分等指标，帮助管理员识别需要优先优化的内容。

第四章：对话配置

对话配置影响系统的对话行为和交互体验。主要配置项包括：

欢迎语配置定义用户首次访问时看到的问候信息，好的欢迎语应该简洁明了，告知用户可以提供什么帮助。

意图识别配置定义系统需要识别的用户意图类型，如咨询、投诉、建议、闲聊等。不同意图可以触发不同的处理流程。

转人工规则配置定义何时应该将对话转接到人工客服。常见转人工条件包括：用户明确要求转人工、问题多次未能解决、用户情绪负面、涉及敏感操作等。

答案生成配置影响回复的风格和格式。可以配置回复的最大长度、是否显示信息来源、是否使用表情符号等。

第五章：数据统计

系统提供完善的数据统计分析功能，帮助企业了解客服运营状况。

对话统计包括每日对话量、对话时长、解决的问题数、解决率等核心指标。这些数据可以帮助企业评估客服工作效率和系统使用情况。

用户反馈统计收集用户对每次回复的满意度评价，包括满意、一般、不满意三个等级。不满意评价应重点分析原因，针对性优化知识库或系统配置。

热点问题分析自动统计高频访问的问题，帮助企业了解用户关注的焦点。这些热点问题应该是知识库建设的优先内容。

第六章：系统集成

智能客服系统支持多种集成方式，方便与企业现有系统对接。

API集成提供RESTful接口，允许企业系统通过HTTP请求调用客服功能。可以将智能客服嵌入网站、移动APP、微信公众号等多种渠道。

SDK集成提供客户端开发包，支持iOS、Android、小程序等平台的原生开发，实现更深度定制和更好的用户体验。

第三方系统对接支持与企业CRM、工单系统、知识库系统等对接，实现数据互通和流程协同。

第七章：使用注意事项

为保证系统稳定运行和服务质量，请注意以下事项：

知识库内容应该准确、规范，避免模糊或歧义性表述。同一问题应有统一的答案格式，便于系统学习和用户理解。

定期检查系统日志和统计数据，及时发现和处理异常情况。对于系统无法解决的问题，应及时补充相关知识条目。

敏感信息和隐私数据不应添加到知识库中，如涉及此类问题应及时转人工处理。

系统升级维护应选择在业务低峰期进行，提前通知用户并做好回滚准备。`

const DEFAULT_QUERY = '如何将客服系统集成到APP中？'

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
