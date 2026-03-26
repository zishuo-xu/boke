import { useState } from 'react'
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
            <span className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>Query 向量</span>
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
            {queryVector.map((val, i) => (
              <div
                key={i}
                className="w-8 h-8 flex items-center justify-center text-xs rounded"
                style={{
                  backgroundColor: `rgba(59, 130, 246, ${Math.abs(val) * 0.5 + 0.1})`,
                  color: val > 0 ? 'rgb(147, 197, 253)' : 'rgb(255, 200, 200)'
                }}
              >
                {val.toFixed(1)}
              </div>
            ))}
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
            <div
              key={chunk.id}
              className={`
                rounded-lg p-4 transition-all
                ${isTopK
                  ? isDark
                    ? 'bg-blue-600/10 border border-blue-500/50'
                    : 'bg-blue-50 border border-blue-200'
                  : isDark
                    ? 'bg-dark-900/50 border border-dark-700 opacity-50'
                    : 'bg-gray-50 border border-gray-200 opacity-60'
                }
              `}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  {isTopK && (
                    <span className={`w-6 h-6 text-xs rounded-full flex items-center justify-center font-bold ${isDark ? 'bg-blue-600 text-white' : 'bg-blue-500 text-white'}`}>
                      {rank}
                    </span>
                  )}
                  <span className={`text-xs font-mono ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{chunk.id}</span>
                </div>
                <div className="flex items-center gap-4">
                  {result && (
                    <span className={`
                      text-sm font-bold
                      ${result.similarity > 0.7 ? 'text-green-400' :
                        result.similarity > 0.4 ? 'text-yellow-400' : isDark ? 'text-gray-400' : 'text-gray-500'}
                    `}>
                      {result.similarity.toFixed(3)}
                    </span>
                  )}
                  {!isTopK && (
                    <span className={`text-xs ${isDark ? 'text-dark-600' : 'text-gray-400'}`}>未命中</span>
                  )}
                </div>
              </div>
              <p className={`text-sm line-clamp-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{chunk.text}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}
