import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Chunk, RetrievalResult } from '../../App'

interface StepRetrievalProps {
  chunks: Chunk[]
  retrievalResults: RetrievalResult[]
  queryVector: number[]
  topK: number
  theme?: 'dark' | 'light'
}

export default function StepRetrieval({
  chunks,
  retrievalResults,
  queryVector,
  topK,
  theme = 'dark'
}: StepRetrievalProps) {
  const isDark = theme === 'dark'
  const [queryExpanded, setQueryExpanded] = useState(false)
  const getChunkById = (id: string) => chunks.find(c => c.id === id)

  return (
    <div className="h-full">
      <div className={`text-sm mb-4 ${isDark ? 'text-dark-500' : 'text-gray-500'}`}>
        召回 <span className="text-blue-400 font-bold">Top-{topK}</span> 个最相关的 chunk
      </div>

      {/* Query Vector - Collapsible */}
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

      {/* Results */}
      <div className="space-y-3">
        {chunks.map((chunk, index) => {
          const result = retrievalResults.find(r => r.chunk_id === chunk.id)
          const isTopK = result !== undefined
          const rank = retrievalResults.findIndex(r => r.chunk_id === chunk.id) + 1

          return (
            <motion.div
              key={chunk.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{
                opacity: isTopK ? 1 : 0.5,
                x: 0,
                backgroundColor: isTopK
                  ? (isDark ? 'rgba(59, 130, 246, 0.1)' : 'rgba(59, 130, 246, 0.08)')
                  : (isDark ? 'rgba(30, 30, 30, 0.5)' : 'rgba(249, 250, 251, 0.5)')
              }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              className={`
                rounded-lg p-4 border transition-all
                ${isTopK
                  ? isDark
                    ? 'border-blue-500/50'
                    : 'border-blue-300'
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
                      className={`w-6 h-6 text-xs rounded-full flex items-center justify-center font-bold ${isDark ? 'bg-blue-600 text-white' : 'bg-blue-500 text-white'}`}
                    >
                      {rank}
                    </motion.span>
                  )}
                  <span className={`text-xs font-mono ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{chunk.id}</span>
                </div>
                <div className="flex items-center gap-4">
                  {result && (
                    <motion.span
                      initial={{ scale: 0.5, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ delay: index * 0.1 + 0.3, type: "spring" }}
                      className={`
                        text-sm font-bold
                        ${result.similarity > 0.7 ? 'text-green-400' :
                          result.similarity > 0.4 ? 'text-yellow-400' : isDark ? 'text-gray-400' : 'text-gray-500'}
                      `}
                    >
                      {result.similarity.toFixed(3)}
                    </motion.span>
                  )}
                  {!isTopK && (
                    <span className={`text-xs ${isDark ? 'text-dark-600' : 'text-gray-400'}`}>未命中</span>
                  )}
                </div>
              </div>
              <p className={`text-sm line-clamp-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{chunk.text}</p>

              {/* 相似度条形指示器 */}
              {result && (
                <div className="mt-2 h-1 rounded-full overflow-hidden bg-dark-700">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${result.similarity * 100}%` }}
                    transition={{ duration: 0.5, delay: index * 0.1 + 0.4, ease: "easeOut" }}
                    className={`h-full rounded-full ${
                      result.similarity > 0.7 ? 'bg-green-500' :
                      result.similarity > 0.4 ? 'bg-yellow-500' : 'bg-gray-500'
                    }`}
                  />
                </div>
              )}
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
