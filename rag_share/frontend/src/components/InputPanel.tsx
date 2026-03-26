import { ProcessRequest } from '../App'

interface InputPanelProps {
  inputData: ProcessRequest
  setInputData: (data: ProcessRequest) => void
  onProcess: () => void
  isProcessing: boolean
  hasResult: boolean
  theme?: 'dark' | 'light'
}

export default function InputPanel({
  inputData,
  setInputData,
  onProcess,
  isProcessing,
  hasResult,
  theme = 'dark'
}: InputPanelProps) {
  const isDark = theme === 'dark'

  return (
    <div className={`rounded-xl p-4 h-full flex flex-col gap-4 ${isDark ? 'bg-dark-800' : 'bg-white border border-gray-200'}`}>
      <h2 className={`text-lg font-semibold border-b pb-2 ${isDark ? 'text-white border-dark-700' : 'text-gray-900 border-gray-200'}`}>输入配置</h2>

      {/* Original Text */}
      <div>
        <label className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>原始文本</label>
        <textarea
          value={inputData.text}
          onChange={(e) => setInputData({ ...inputData, text: e.target.value })}
          className={`w-full h-32 rounded-lg p-3 text-sm resize-none focus:outline-none focus:border-blue-500 ${isDark ? 'bg-dark-900 border-dark-700 text-gray-200' : 'bg-gray-50 border-gray-300 text-gray-900'}`}
          placeholder="输入知识库文本..."
        />
      </div>

      {/* Query */}
      <div>
        <label className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>用户问题</label>
        <input
          type="text"
          value={inputData.query}
          onChange={(e) => setInputData({ ...inputData, query: e.target.value })}
          className={`w-full rounded-lg p-3 text-sm focus:outline-none focus:border-blue-500 ${isDark ? 'bg-dark-900 border-dark-700 text-gray-200' : 'bg-gray-50 border-gray-300 text-gray-900'}`}
          placeholder="输入查询问题..."
        />
      </div>

      {/* Parameters */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Chunk Size</label>
          <input
            type="number"
            value={inputData.chunk_size}
            onChange={(e) => setInputData({ ...inputData, chunk_size: parseInt(e.target.value) || 50 })}
            className={`w-full rounded-lg p-2 text-sm focus:outline-none focus:border-blue-500 ${isDark ? 'bg-dark-900 border-dark-700 text-gray-200' : 'bg-gray-50 border-gray-300 text-gray-900'}`}
          />
        </div>
        <div>
          <label className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Overlap</label>
          <input
            type="number"
            value={inputData.overlap}
            onChange={(e) => setInputData({ ...inputData, overlap: parseInt(e.target.value) || 10 })}
            className={`w-full rounded-lg p-2 text-sm focus:outline-none focus:border-blue-500 ${isDark ? 'bg-dark-900 border-dark-700 text-gray-200' : 'bg-gray-50 border-gray-300 text-gray-900'}`}
          />
        </div>
        <div>
          <label className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Top K</label>
          <input
            type="number"
            value={inputData.top_k}
            onChange={(e) => setInputData({ ...inputData, top_k: parseInt(e.target.value) || 3 })}
            className={`w-full rounded-lg p-2 text-sm focus:outline-none focus:border-blue-500 ${isDark ? 'bg-dark-900 border-dark-700 text-gray-200' : 'bg-gray-50 border-gray-300 text-gray-900'}`}
          />
        </div>
        <div>
          <label className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>切片方式</label>
          <select
            value={inputData.chunking_strategy}
            onChange={(e) => setInputData({ ...inputData, chunking_strategy: e.target.value })}
            className={`w-full rounded-lg p-2 text-sm focus:outline-none focus:border-blue-500 ${isDark ? 'bg-dark-900 border-dark-700 text-gray-200' : 'bg-gray-50 border-gray-300 text-gray-900'}`}
          >
            <option value="by_chars">按字符</option>
            <option value="by_sentence">按句子</option>
            <option value="by_paragraph">按段落</option>
          </select>
        </div>
      </div>

      <div className="flex items-center">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={inputData.use_rerank}
            onChange={(e) => setInputData({ ...inputData, use_rerank: e.target.checked })}
            className="w-4 h-4 rounded border-dark-600 bg-dark-900 text-blue-600 focus:ring-blue-500"
          />
          <span className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>启用重排</span>
        </label>
      </div>

      {/* Process Button */}
      <button
        onClick={onProcess}
        disabled={isProcessing || !inputData.text || !inputData.query}
        className={`
          w-full py-3 rounded-lg font-medium transition-all
          ${isProcessing
            ? isDark ? 'bg-dark-700 text-dark-500' : 'bg-gray-200 text-gray-400'
            : 'bg-blue-600 text-white hover:bg-blue-500 shadow-lg shadow-blue-600/30'
          }
        `}
      >
        {isProcessing ? '处理中...' : hasResult ? '重新开始演示' : '开始演示'}
      </button>

      {/* Quick Fill */}
      <button
        onClick={() => setInputData({
          text: `人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，致力于开发能够执行通常需要人类智能的任务的系统。这包括视觉感知、语音识别、决策制定和语言翻译等。

机器学习是人工智能的一个子集，它使系统能够从数据中学习并改进性能，而无需明确编程。深度学习则是机器学习的一个分支，使用多层神经网络来分析各种因素的数据。

大型语言模型（LLM）是深度学习在自然语言处理领域的应用，能够理解和生成人类语言。检索增强生成（RAG）技术结合了检索系统和生成模型，提高了AI系统的准确性和可靠性。`,
          query: '什么是RAG技术？',
          chunk_size: 50,
          overlap: 10,
          top_k: 3,
          use_rerank: true,
          chunking_strategy: 'by_chars'
        })}
        className={`text-sm ${isDark ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-700'} underline`}
      >
        填充示例内容
      </button>
    </div>
  )
}
