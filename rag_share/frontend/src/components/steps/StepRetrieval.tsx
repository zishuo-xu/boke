import { useState } from 'react'
import { motion } from 'framer-motion'
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
  const [showFulltextOnly, setShowFulltextOnly] = useState(false)

  const isHybrid = searchMode === 'hybrid' && retrievalResults.some(r => r.vector_score !== undefined && r.fulltext_score !== undefined)

  // 显示模式
  let displayMode: 'vector' | 'fulltext' | 'fused' = 'fused'
  if (showVectorOnly) displayMode = 'vector'
  if (showFulltextOnly) displayMode = 'fulltext'

  // 根据显示模式确定颜色
  const getColor = (mode: 'vector' | 'fulltext' | 'fused') => {
    switch (mode) {
      case 'vector': return { bg: 'blue', text: 'text-blue-400', bar: 'bg-blue-500' }
      case 'fulltext': return { bg: 'green', text: 'text-green-400', bar: 'bg-green-500' }
      case 'fused': return { bg: 'purple', text: 'text-purple-400', bar: 'bg-purple-500' }
    }
  }

  const colors = getColor(displayMode)

  return (
    <div className="h-full">
      <div className={`text-sm mb-4 ${isDark ? 'text-dark-500' : 'text-gray-500'}`}>
        召回 <span className="text-blue-400 font-bold">Top-{topK}</span> 个最相关的 chunk
        {isHybrid && <span className="ml-2 text-green-400">(混合检索模式)</span>}
      </div>

      {/* Query Vector */}
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
            onClick={() => { setShowVectorOnly(true); setShowFulltextOnly(false); }}
            className={`px-3 py-1 text-xs rounded ${showVectorOnly && !showFulltextOnly ? 'bg-blue-600 text-white' : isDark ? 'bg-dark-700 text-gray-300' : 'bg-gray-200 text-gray-700'}`}
          >
            第一路：向量检索
          </button>
          <button
            onClick={() => { setShowFulltextOnly(true); setShowVectorOnly(false); }}
            className={`px-3 py-1 text-xs rounded ${showFulltextOnly && !showVectorOnly ? 'bg-green-600 text-white' : isDark ? 'bg-dark-700 text-gray-300' : 'bg-gray-200 text-gray-700'}`}
          >
            第二路：全文检索
          </button>
          <button
            onClick={() => { setShowVectorOnly(false); setShowFulltextOnly(false); }}
            className={`px-3 py-1 text-xs rounded ${!showVectorOnly && !showFulltextOnly ? 'bg-purple-600 text-white' : isDark ? 'bg-dark-700 text-gray-300' : 'bg-gray-200 text-gray-700'}`}
          >
            RRF 融合结果
          </button>
        </div>
      )}

      {/* 显示模式说明 */}
      {isHybrid && (
        <div className={`text-xs mb-3 p-2 rounded ${isDark ? 'bg-dark-800 text-gray-400' : 'bg-gray-100 text-gray-600'}`}>
          {displayMode === 'vector' && '【第一路召回】向量语义检索：基于 HNSW 索引，匹配"智能客服"、"APP"等语义概念'}
          {displayMode === 'fulltext' && '【第二路召回】全文关键词检索：基于 PostgreSQL TS_RANK，精确匹配"集成"、"APP"等关键词'}
          {displayMode === 'fused' && '【结果融合】RRF 算法：结合向量排名和全文排名，向量权重 60%，全文权重 40%'}
        </div>
      )}

      {/* 结果列表 */}
      <div className="space-y-3">
        {chunks.map((chunk, index) => {
          const result = retrievalResults.find(r => r.chunk_id === chunk.id)
          const isTopK = result !== undefined
          const rank = retrievalResults.findIndex(r => r.chunk_id === chunk.id) + 1

          // 根据显示模式确定分数
          let displayScore = result?.similarity ?? 0
          if (displayMode === 'vector') {
            displayScore = result?.vector_score ?? 0
          } else if (displayMode === 'fulltext') {
            displayScore = result?.fulltext_score ?? 0
          }

          return (
            <motion.div
              key={chunk.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{
                opacity: isTopK ? 1 : 0.5,
                x: 0,
                backgroundColor: isTopK
                  ? (isDark ? `rgba(59, 130, 246, 0.08)` : `rgba(59, 130, 246, 0.05)`)
                  : (isDark ? 'rgba(30, 30, 30, 0.5)' : 'rgba(249, 250, 251, 0.5)')
              }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              className={`
                rounded-lg p-4 border transition-all
                ${isTopK
                  ? isDark ? 'border-blue-500/30' : 'border-blue-300'
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
                        isDark ? 'bg-blue-600 text-white' : 'bg-blue-500 text-white'
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
                      <span className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                        {displayMode === 'vector' ? '向量' : displayMode === 'fulltext' ? '全文' : '融合'}
                      </span>
                      <motion.span
                        initial={{ scale: 0.5, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ delay: index * 0.1 + 0.3, type: "spring" }}
                        className={`text-sm font-bold ${colors.text}`}
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
                      {/* 向量分数条 */}
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
                      {/* 全文分数条 */}
                      <div className="flex items-center gap-2 text-xs">
                        <span className="w-10 text-green-400">全文</span>
                        <div className="flex-1 h-1 rounded-full overflow-hidden bg-dark-700">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${(result.fulltext_score ?? 0) * 100}%` }}
                            transition={{ duration: 0.5, delay: index * 0.1 + 0.5, ease: "easeOut" }}
                            className="h-full rounded-full bg-green-500"
                          />
                        </div>
                        <span className="w-12 text-right text-green-400">{(result.fulltext_score ?? 0).toFixed(3)}</span>
                      </div>
                      {/* 融合分数条 */}
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
