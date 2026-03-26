import { Chunk, RetrievalResult, RerankedResult } from '../../App'

interface StepRerankProps {
  chunks: Chunk[]
  retrievalResults: RetrievalResult[]
  rerankedResults: RerankedResult[] | null
  useRerank: boolean
  theme?: 'dark' | 'light'
}

export default function StepRerank({
  chunks,
  retrievalResults,
  rerankedResults,
  useRerank,
  theme = 'dark'
}: StepRerankProps) {
  const isDark = theme === 'dark'

  if (!useRerank) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 ${isDark ? 'bg-dark-700' : 'bg-gray-200'}`}>
            <svg className={`w-8 h-8 ${isDark ? 'text-dark-500' : 'text-gray-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
          </div>
          <h3 className={`text-xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>重排已禁用</h3>
          <p className={isDark ? 'text-dark-500' : 'text-gray-400'}>本次演示跳过了重排步骤</p>
        </div>
      </div>
    )
  }

  const getChunkById = (id: string) => chunks.find(c => c.id === id)

  return (
    <div className="h-full">
      <div className={`text-sm mb-4 ${isDark ? 'text-dark-500' : 'text-gray-500'}`}>
        对召回结果进行重排，优化排序
      </div>

      <div className="flex gap-6">
        {/* Before Rerank */}
        <div className="flex-1">
          <div className={`text-xs mb-2 ${isDark ? 'text-dark-500' : 'text-gray-500'}`}>初始排序</div>
          <div className="space-y-2">
            {retrievalResults.map((result, index) => {
              const chunk = getChunkById(result.chunk_id)
              return (
                <div key={result.chunk_id} className={`rounded-lg p-3 ${isDark ? 'bg-dark-900' : 'bg-gray-50'}`}>
                  <div className="flex items-center justify-between mb-1">
                    <span className={`text-xs font-mono ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>#{index + 1}</span>
                    <span className={`text-xs ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>{result.similarity.toFixed(3)}</span>
                  </div>
                  <p className={`text-sm line-clamp-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{chunk?.text}</p>
                </div>
              )
            })}
          </div>
        </div>

        {/* Arrow */}
        <div className="flex items-center">
          <div className="w-10 h-10 bg-purple-600/20 rounded-full flex items-center justify-center">
            <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </div>
        </div>

        {/* After Rerank */}
        <div className="flex-1">
          <div className={`text-xs mb-2 ${isDark ? 'text-dark-500' : 'text-gray-500'}`}>重排后</div>
          <div className="space-y-2">
            {(rerankedResults || []).map((result) => {
              const chunk = getChunkById(result.chunk_id)
              const moved = result.original_rank !== result.new_rank
              return (
                <div key={result.chunk_id} className={`rounded-lg p-3 border ${isDark ? 'bg-dark-900 border-purple-500/30' : 'bg-gray-50 border-purple-200'}`}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-mono ${isDark ? 'text-purple-400' : 'text-purple-600'}`}>#{result.new_rank}</span>
                      {moved && (
                        <span className="text-xs text-yellow-500">
                          ↑ {result.original_rank - result.new_rank > 0 ? '+' : ''}{result.original_rank - result.new_rank}
                        </span>
                      )}
                    </div>
                    <span className={`text-xs ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>{result.similarity.toFixed(3)}</span>
                  </div>
                  <p className={`text-sm line-clamp-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{chunk?.text}</p>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
