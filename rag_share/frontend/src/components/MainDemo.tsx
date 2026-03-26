import { ProcessRequest, RagProcessResult, Chunk } from '../App'
import StepOriginalText from './steps/StepOriginalText'
import StepPreprocessing from './steps/StepPreprocessing'
import StepChunking from './steps/StepChunking'
import StepVectorization from './steps/StepVectorization'
import StepQuery from './steps/StepQuery'
import StepRetrieval from './steps/StepRetrieval'
import StepRerank from './steps/StepRerank'
import StepPrompt from './steps/StepPrompt'
import StepAnswer from './steps/StepAnswer'

interface MainDemoProps {
  currentStep: number
  inputData: ProcessRequest
  result: RagProcessResult | null
  editedChunks: Chunk[] | null
  setEditedChunks: (chunks: Chunk[] | null) => void
  theme?: 'dark' | 'light'
}

export default function MainDemo({ currentStep, inputData, result, editedChunks, setEditedChunks, theme = 'dark' }: MainDemoProps) {
  const isDark = theme === 'dark'
  const renderStep = () => {
    if (currentStep === 1) {
      return <StepOriginalText text={inputData.text} theme={theme} />
    }

    if (!result) {
      return (
        <div className={`flex items-center justify-center h-full ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>
          请先点击"开始演示"加载数据
        </div>
      )
    }

    // 用于后续步骤的 chunks（优先使用编辑后的）
    const activeChunks = editedChunks || result.chunks

    switch (currentStep) {
      case 2:
        return <StepPreprocessing original={inputData.text} preprocessed={result.preprocessed_text} theme={theme} />
      case 3:
        return (
          <StepChunking
            chunks={result.chunks}
            editedChunks={editedChunks}
            onChunksChange={setEditedChunks}
            theme={theme}
          />
        )
      case 4:
        return <StepVectorization chunks={activeChunks} vectors={result.vectors} queryVector={result.query_vector} theme={theme} />
      case 5:
        return <StepQuery query={inputData.query} theme={theme} />
      case 6:
        return (
          <StepRetrieval
            chunks={activeChunks}
            retrievalResults={result.retrieval_results}
            queryVector={result.query_vector}
            topK={inputData.top_k}
            theme={theme}
          />
        )
      case 7:
        return (
          <StepRerank
            chunks={activeChunks}
            retrievalResults={result.retrieval_results}
            rerankedResults={result.reranked_results}
            useRerank={inputData.use_rerank}
            query={inputData.query}
            theme={theme}
          />
        )
      case 8:
        return <StepPrompt prompt={result.prompt} theme={theme} />
      case 9:
        return <StepAnswer answer={result.answer} theme={theme} />
      default:
        return null
    }
  }

  return (
    <div className={`rounded-xl p-6 h-full flex flex-col ${isDark ? 'bg-dark-800' : 'bg-white border border-gray-200'}`}>
      <div className="flex items-center justify-between mb-4">
        <h2 className={`text-xl font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
          步骤 {currentStep}: {['原始文本', '预处理', '切片', '向量化', '用户提问', '相似度检索', '重排', 'Prompt 组装', '答案生成'][currentStep - 1]}
        </h2>
        {editedChunks && (
          <span className={`text-xs px-2 py-1 rounded ${isDark ? 'text-yellow-400 bg-yellow-400/10' : 'text-yellow-600 bg-yellow-100'}`}>
            已编辑切片
          </span>
        )}
      </div>
      <div className="flex-1 overflow-auto">
        {renderStep()}
      </div>
    </div>
  )
}
