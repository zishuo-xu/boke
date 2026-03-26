import { useMemo } from 'react'
import { motion } from 'framer-motion'
import { Chunk, RetrievalResult, RerankedResult } from '../../App'

interface StepRerankProps {
  chunks: Chunk[]
  retrievalResults: RetrievalResult[]
  rerankedResults: RerankedResult[] | null
  useRerank: boolean
  query?: string
  theme?: 'dark' | 'light'
}

// 简化的 BM25 计算（用于可视化）
function calculateBM25Score(query: string, chunkText: string): number {
  if (!query || !chunkText) return 0

  // 简单2-gram分词
  const tokenize = (text: string) => {
    const cleaned = text.replace(/[^\w\u4e00-\u9fff]/g, '')
    const tokens: string[] = []
    for (let i = 0; i < cleaned.length - 1; i++) {
      tokens.push(cleaned.slice(i, i + 2))
    }
    return tokens
  }

  const queryTokens = tokenize(query)
  const docTokens = tokenize(chunkText)

  if (queryTokens.length === 0) return 0

  // 计算词频
  const docTF: Record<string, number> = {}
  for (const token of docTokens) {
    docTF[token] = (docTF[token] || 0) + 1
  }

  // 计算 BM25 分数（简化版）
  let score = 0
  for (const qToken of queryTokens) {
    if (docTF[qToken]) {
      const tf = docTF[qToken]
      score += tf / (tf + 1.5) // 简化的词频饱和
    }
  }

  return score / queryTokens.length
}

export default function StepRerank({
  chunks,
  retrievalResults,
  rerankedResults,
  useRerank,
  query = '',
  theme = 'dark'
}: StepRerankProps) {
  const isDark = theme === 'dark'

  if (!useRerank) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 ${isDark ? 'bg-dark-700' : 'bg-gray-200'}`}
          >
            <svg className={`w-8 h-8 ${isDark ? 'text-dark-500' : 'text-gray-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
          </motion.div>
          <h3 className={`text-xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>重排已禁用</h3>
          <p className={isDark ? 'text-dark-500' : 'text-gray-400'}>本次演示跳过了重排步骤</p>
        </div>
      </div>
    )
  }

  const getChunkById = (id: string) => chunks.find(c => c.id === id)

  // 计算每个 chunk 的 BM25 和 向量分数（用于可视化）
  const scoreDetails = useMemo(() => {
    if (!query) return []

    const results = (rerankedResults || retrievalResults).map(result => {
      const chunk = getChunkById(result.chunk_id)
      const bm25Score = calculateBM25Score(query, chunk?.text || '')
      const vectorScore = result.similarity

      // 归一化
      const maxBM25 = 1
      const maxVec = 1

      return {
        chunkId: result.chunk_id,
        bm25: bm25Score,
        bm25Norm: Math.min(bm25Score / maxBM25, 1),
        vector: vectorScore,
        vectorNorm: vectorScore,
        fused: 0.4 * Math.min(bm25Score / maxBM25, 1) + 0.6 * vectorScore
      }
    })

    // 重新排序
    results.sort((a, b) => b.fused - a.fused)

    return results
  }, [rerankedResults, retrievalResults, query, chunks])

  return (
    <div className="h-full flex flex-col gap-4">
      {/* 标题 */}
      <div className={`text-sm ${isDark ? 'text-dark-500' : 'text-gray-500'}`}>
        BM25 + 向量相似度 融合排序
      </div>

      {/* 公式说明 */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`rounded-lg p-3 border ${isDark ? 'bg-purple-500/5 border-purple-500/30' : 'bg-purple-50 border-purple-200'}`}
      >
        <div className={`text-xs mb-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>融合公式</div>
        <div className="flex items-center gap-3 text-sm">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 font-mono">0.4</span>
            <span className={isDark ? 'text-gray-400' : 'text-gray-600'}>× BM25</span>
          </div>
          <span className={isDark ? 'text-gray-500' : 'text-gray-400'}>+</span>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-green-500/20 text-green-400 font-mono">0.6</span>
            <span className={isDark ? 'text-gray-400' : 'text-gray-600'}>× 向量相似度</span>
          </div>
          <span className={isDark ? 'text-gray-500' : 'text-gray-400'}>=</span>
          <span className="font-mono text-purple-400">融合分数</span>
        </div>
      </motion.div>

      {/* 分数分解可视化 */}
      <div className="flex-1 overflow-auto">
        <div className="space-y-3">
          {scoreDetails.map((item, index) => {
            const chunk = getChunkById(item.chunkId)
            const originalIndex = retrievalResults.findIndex(r => r.chunk_id === item.chunkId)
            const moved = originalIndex !== -1 && originalIndex !== index

            return (
              <motion.div
                key={item.chunkId}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`rounded-lg p-4 border ${isDark ? 'bg-dark-900 border-dark-700' : 'bg-gray-50 border-gray-200'}`}
              >
                {/* Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <motion.span
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: index * 0.1 + 0.2, type: "spring" }}
                      className={`w-6 h-6 text-xs rounded-full flex items-center justify-center font-bold ${
                        isDark ? 'bg-purple-600 text-white' : 'bg-purple-500 text-white'
                      }`}
                    >
                      {index + 1}
                    </motion.span>
                    <span className={`text-xs font-mono px-2 py-1 rounded ${isDark ? 'text-blue-400 bg-blue-400/10' : 'text-blue-600 bg-blue-50'}`}>
                      {item.chunkId}
                    </span>
                    {moved && (
                      <span className="text-xs text-yellow-500">
                        原排名 #{originalIndex + 1}
                      </span>
                    )}
                  </div>
                  <div className="text-right">
                    <span className="text-lg font-bold text-purple-400">{item.fused.toFixed(3)}</span>
                  </div>
                </div>

                {/* 分数条 */}
                <div className="space-y-2">
                  {/* BM25 分数 */}
                  <div className="flex items-center gap-3">
                    <div className="w-20 flex items-center gap-1">
                      <span className="text-xs px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400">BM25</span>
                    </div>
                    <div className="flex-1 h-3 rounded-full overflow-hidden bg-dark-700">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${item.bm25Norm * 100}%` }}
                        transition={{ duration: 0.5, delay: index * 0.1 + 0.3 }}
                        className="h-full rounded-full bg-blue-500"
                      />
                    </div>
                    <span className="w-16 text-right text-xs font-mono text-blue-400">{item.bm25.toFixed(3)}</span>
                    <span className="w-8 text-right text-xs text-gray-500">×0.4</span>
                  </div>

                  {/* 向量分数 */}
                  <div className="flex items-center gap-3">
                    <div className="w-20 flex items-center gap-1">
                      <span className="text-xs px-1.5 py-0.5 rounded bg-green-500/20 text-green-400">向量</span>
                    </div>
                    <div className="flex-1 h-3 rounded-full overflow-hidden bg-dark-700">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${item.vectorNorm * 100}%` }}
                        transition={{ duration: 0.5, delay: index * 0.1 + 0.4 }}
                        className="h-full rounded-full bg-green-500"
                      />
                    </div>
                    <span className="w-16 text-right text-xs font-mono text-green-400">{item.vector.toFixed(3)}</span>
                    <span className="w-8 text-right text-xs text-gray-500">×0.6</span>
                  </div>
                </div>

                {/* 融合结果 */}
                <div className={`mt-3 pt-3 border-t ${isDark ? 'border-dark-700' : 'border-gray-200'}`}>
                  <div className="flex items-center justify-between text-sm">
                    <span className={isDark ? 'text-gray-500' : 'text-gray-500'}>融合分数</span>
                    <span className="font-mono font-bold text-purple-400">
                      0.4×{item.bm25.toFixed(2)} + 0.6×{item.vector.toFixed(2)} = {item.fused.toFixed(3)}
                    </span>
                  </div>
                </div>

                {/* 文本预览 */}
                <p className={`mt-2 text-sm line-clamp-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  {chunk?.text}
                </p>
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* 图例 */}
      <div className={`flex items-center gap-4 text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded bg-blue-500"></div>
          <span>BM25（关键词匹配）</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded bg-green-500"></div>
          <span>向量相似度（语义匹配）</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded bg-purple-500"></div>
          <span>融合分数</span>
        </div>
      </div>
    </div>
  )
}
