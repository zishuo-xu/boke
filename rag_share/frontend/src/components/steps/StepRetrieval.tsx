import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Chunk, RetrievalResult } from '../../App'

interface StepRetrievalProps {
  chunks: Chunk[]
  retrievalResults: RetrievalResult[]
  queryVector: number[]
  topK: number
  searchMode?: string
  theme?: 'dark' | 'light'
}

export default function StepRetrieval({
  chunks,
  retrievalResults,
  queryVector,
  topK,
  searchMode = 'vector',
  theme = 'dark'
}: StepRetrievalProps) {
  const isDark = theme === 'dark'
  const [queryExpanded, setQueryExpanded] = useState(false)
  const [showVectorOnly, setShowVectorOnly] = useState(false)
  const [showBm25Only, setShowBm25Only] = useState(false)
  const getChunkById = (id: string) => chunks.find(c => c.id === id)

  const isHybrid = searchMode === 'hybrid' && retrievalResults.some(r => r.vector_score !== undefined && r.bm25_score !== undefined)

  // 分离向量分数和BM25分数
  const vectorResults = retrievalResults.map(r => ({
    ...r,
    displayScore: r.vector_score ?? r.similarity
  }))

  const bm25Results = retrievalResults
    .filter(r => r.bm25_score !== undefined)
    .sort((a, b) => (b.bm25_score ?? 0) - (a.bm25_score ?? 0))

  return (
    <div className="h-full">
      <div className={`text-sm mb-4 ${isDark ? 'text-dark-500' : 'text-gray-500'}`}>
        召回 <span className="text-blue-400 font-bold">Top-{topK}</span> 个最相关的 chunk
        {isHybrid && <span className="ml-2 text-green-400">(混合检索模式)</span>}
      </div>

      {/* 查询向量 */}
      <details
        className={`rounded-lg mb-4 border ${isDark ? 'bg-dark-900 border-dark-700' : 'bg-gray-50 border-gray-200'}`}
        open={queryExpanded}
      >
        <summary
          className={`p-3 cursor-pointer list-none flex items-center justify-between ${isDark ? 'hover:bg-dark-800' : 'hover:bg-gray-100'}`}
          onClick={() => setQueryExpanded(!queryExpanded)}
        >
          <div className="flex items-center gap-2">
            <motion.span
              animate={{ rotate: queryExpanded ? 180 : 0 }}
              className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'}`}
            >
              Query 向量
            </motion.span>
            <span className={`text-xs ${isDark ? 'text-dark-600' : 'text-gray-400'}`}>({queryVector.length}维)</span>
          </div>
          <svg
            className={`w-4 h-4 transition-transform ${queryExpanded ? 'rotate-180' : ''} ${isDark ? 'text-dark-500' : 'text-gray-400'}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </summary>
        <div className="px-3 pb-3">
          <div className="flex flex-wrap gap-1">
            {queryVector.slice(0, 40).map((val, i) => (
              <motion.div
                key={i}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: i * 0.02 }}
                className="w-7 h-7 flex items-center justify-center text-xs rounded"
                style={{
                  backgroundColor: val > 0
                    ? `rgba(59, 130, 246, ${Math.abs(val) * 0.6 + 0.2})`
                    : `rgba(239, 68, 68, ${Math.abs(val) * 0.4 + 0.2})`,
                  color: Math.abs(val) > 0.5 ? 'white' : (isDark ? '#9ca3af' : '#6b7280')
                }}
              >
                {val > 0 ? '+' : ''}{val.toFixed(1)}
              </motion.div>
            ))}
            {queryVector.length > 40 && (
              <span className={`text-xs self-center ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>
                +{queryVector.length - 40} 维
              </span>
            )}
          </div>
        </div>
      </details>

      {/* 混合检索切换按钮 */}
      {isHybrid && (
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => { setShowVectorOnly(true); setShowBm25Only(false); }}
            className={`px-3 py-1 text-xs rounded ${showVectorOnly && !showBm25Only ? 'bg-blue-600 text-white' : isDark ? 'bg-dark-700 text-gray-300' : 'bg-gray-200 text-gray-700'}`}
          >
            向量检索
          </button>
          <button
            onClick={() => { setShowBm25Only(true); setShowVectorOnly(false); }}
            className={`px-3 py-1 text-xs rounded ${showBm25Only && !showVectorOnly ? 'bg-green-600 text-white' : isDark ? 'bg-dark-700 text-gray-300' : 'bg-gray-200 text-gray-700'}`}
          >
            BM25 检索
          </button>
          <button
            onClick={() => { setShowVectorOnly(false); setShowBm25Only(false); }}
            className={`px-3 py-1 text-xs rounded ${!showVectorOnly && !showBm25Only ? 'bg-purple-600 text-white' : isDark ? 'bg-dark-700 text-gray-300' : 'bg-gray-200 text-gray-700'}`}
          >
            融合结果
          </button>
        </div>
      )}

      {/* 显示模式说明 */}
      {isHybrid && (
        <div className={`text-xs mb-3 p-2 rounded ${isDark ? 'bg-dark-800 text-gray-400' : 'bg-gray-100 text-gray-600'}`}>
          {showVectorOnly && '向量检索：基于语义相似度，匹配"智能客服"、"APP"等概念'}
          {showBm25Only && 'BM25检索：基于关键词匹配，精确匹配"集成"、"APP"等词语'}
          {!showVectorOnly && !showBm25Only && 'RRF融合：结合向量检索和BM25的结果，按排名融合（向量60% + BM25 40%）'}
        </div>
      )}

      {/* 结果列表 */}
      <div className="space-y-3">
        {chunks.map((chunk, index) => {
          const result = retrievalResults.find(r => r.chunk_id === chunk.id)
          const isTopK = result !== undefined
          const rank = retrievalResults.findIndex(r => r.chunk_id === chunk.id) + 1

          // 根据显示模式确定显示的分数
          let displayScore = result?.similarity ?? 0
          let scoreLabel = '融合'
          let scoreColor = 'blue'

          if (showVectorOnly && result?.vector_score !== undefined) {
            displayScore = result.vector_score
            scoreLabel = '向量'
            scoreColor = 'blue'
          } else if (showBm25Only && result?.bm25_score !== undefined) {
            displayScore = result.bm25_score
            scoreLabel = 'BM25'
            scoreColor = 'green'
          }

          return (
            <motion.div
              key={chunk.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{
                opacity: isTopK ? 1 : 0.5,
                x: 0,
                backgroundColor: isTopK
                  ? (showVectorOnly ? (isDark ? 'rgba(59, 130, 246, 0.1)' : 'rgba(59, 130, 246, 0.08)') :
                     showBm25Only ? (isDark ? 'rgba(34, 197, 94, 0.1)' : 'rgba(34, 197, 94, 0.08)') :
                     (isDark ? 'rgba(139, 92, 246, 0.1)' : 'rgba(139, 92, 246, 0.08)'))
                  : (isDark ? 'rgba(30, 30, 30, 0.5)' : 'rgba(249, 250, 251, 0.5)')
              }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              className={`
                rounded-lg p-4 border transition-all
                ${isTopK
                  ? showVectorOnly ? (isDark ? 'border-blue-500/50' : 'border-blue-300') :
                    showBm25Only ? (isDark ? 'border-green-500/50' : 'border-green-300') :
                    (isDark ? 'border-purple-500/50' : 'border-purple-300')
                  : isDark
                    ? 'border-dark-700'
                    : 'border-gray-200'
                }
              `}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  {isTopK && (
                    <motion.span
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: index * 0.1 + 0.2, type: "spring" }}
                      className={`w-6 h-6 text-xs rounded-full flex items-center justify-center font-bold ${
                        showVectorOnly ? (isDark ? 'bg-blue-600 text-white' : 'bg-blue-500 text-white') :
                        showBm25Only ? (isDark ? 'bg-green-600 text-white' : 'bg-green-500 text-white') :
                        (isDark ? 'bg-purple-600 text-white' : 'bg-purple-500 text-white')
                      }`}
                    >
                      {rank}
                    </motion.span>
                  )}
                  <span className={`text-xs font-mono ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{chunk.id}</span>
                </div>
                <div className="flex items-center gap-4">
                  {result && (
                    <>
                      <span className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{scoreLabel}</span>
                      <motion.span
                        initial={{ scale: 0.5, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ delay: index * 0.1 + 0.3, type: "spring" }}
                        className={`text-sm font-bold ${
                          scoreColor === 'blue' ? 'text-blue-400' :
                          scoreColor === 'green' ? 'text-green-400' : 'text-purple-400'
                        }`}
                      >
                        {displayScore.toFixed(3)}
                      </motion.span>
                    </>
                  )}
                  {!isTopK && (
                    <span className={`text-xs ${isDark ? 'text-dark-600' : 'text-gray-400'}`}>未命中</span>
                  )}
                </div>
              </div>
              <p className={`text-sm line-clamp-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{chunk.text}</p>

              {/* 分数条形指示器 */}
              {result && (
                <div className="mt-2 space-y-1">
                  {isHybrid && (
                    <>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="w-10 text-blue-400">向量</span>
                        <div className="flex-1 h-1 rounded-full overflow-hidden bg-dark-700">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${(result.vector_score ?? 0) * 100}%` }}
                            transition={{ duration: 0.5, delay: index * 0.1 + 0.4, ease: "easeOut" }}
                            className="h-full rounded-full bg-blue-500"
                          />
                        </div>
                        <span className="w-12 text-right text-blue-400">{(result.vector_score ?? 0).toFixed(3)}</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="w-10 text-green-400">BM25</span>
                        <div className="flex-1 h-1 rounded-full overflow-hidden bg-dark-700">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${Math.min((result.bm25_score ?? 0) * 20, 100)}%` }}
                            transition={{ duration: 0.5, delay: index * 0.1 + 0.5, ease: "easeOut" }}
                            className="h-full rounded-full bg-green-500"
                          />
                        </div>
                        <span className="w-12 text-right text-green-400">{(result.bm25_score ?? 0).toFixed(1)}</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="w-10 text-purple-400">融合</span>
                        <div className="flex-1 h-1 rounded-full overflow-hidden bg-dark-700">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${result.similarity * 100}%` }}
                            transition={{ duration: 0.5, delay: index * 0.1 + 0.6, ease: "easeOut" }}
                            className="h-full rounded-full bg-purple-500"
                          />
                        </div>
                        <span className="w-12 text-right text-purple-400">{result.similarity.toFixed(3)}</span>
                      </div>
                    </>
                  )}
                  {!isHybrid && (
                    <div className="h-1 rounded-full overflow-hidden bg-dark-700">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${displayScore * 100}%` }}
                        transition={{ duration: 0.5, delay: index * 0.1 + 0.4, ease: "easeOut" }}
                        className={`h-full rounded-full ${
                          displayScore > 0.7 ? 'bg-green-500' :
                          displayScore > 0.4 ? 'bg-yellow-500' : 'bg-gray-500'
                        }`}
                      />
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
