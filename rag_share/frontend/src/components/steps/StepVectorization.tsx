import { useState, useMemo, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Chunk } from '../../App'

interface StepVectorizationProps {
  chunks: Chunk[]
  vectors: number[][]
  queryVector?: number[]
  theme?: 'dark' | 'light'
}

function cosineSimilarity(v1: number[], v2: number[]): number {
  const dot = v1.reduce((sum, a, i) => sum + a * v2[i], 0)
  const norm1 = Math.sqrt(v1.reduce((sum, a) => sum + a * a, 0))
  const norm2 = Math.sqrt(v2.reduce((sum, b) => sum + b * b, 0))
  if (norm1 === 0 || norm2 === 0) return 0
  return dot / (norm1 * norm2)
}

function getHeatmapColor(value: number): string {
  if (value > 0) {
    const intensity = Math.min(value, 1)
    return `rgba(59, 130, 246, ${intensity * 0.8 + 0.2})`
  } else {
    const intensity = Math.min(Math.abs(value), 1)
    return `rgba(239, 68, 68, ${intensity * 0.5 + 0.2})`
  }
}

function getTextColor(value: number): string {
  return value > 0.3 ? 'text-white' : 'text-gray-300'
}

// 固定示例文本
const EXAMPLES = [
  {
    label: '语义相似',
    text1: '人工智能是计算机科学的一个分支',
    text2: 'AI是计算机科学的重要组成部分',
    color: 'blue'
  },
  {
    label: '语义不同',
    text1: '今天天气很好适合出门散步',
    text2: '机器学习需要大量数据训练模型',
    color: 'yellow'
  },
  {
    label: '完全无关',
    text1: '苹果是一种好吃的水果',
    text2: '火箭发射前往太空执行任务',
    color: 'red'
  }
]

// 2D 热力图网格可视化 - 替代条形图
function VectorGrid({ vector, isDark = true, rows = 4, cols = 8 }: { vector: number[], isDark?: boolean, rows?: number, cols?: number }) {
  const total = rows * cols
  const showVector = vector.slice(0, total)

  // 归一化到 0-1 范围用于颜色映射
  const maxAbs = Math.max(...showVector.map(Math.abs), 0.01)

  const cells = showVector.map((val, i) => {
    const intensity = Math.abs(val) / maxAbs
    return { val, intensity, index: i }
  })

  return (
    <div className="space-y-2">
      {/* 图例 */}
      <div className="flex items-center gap-2 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: 'rgba(59, 130, 246, 0.9)' }}></div>
          <span className={isDark ? 'text-gray-400' : 'text-gray-600'}>正值</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: 'rgba(239, 68, 68, 0.9)' }}></div>
          <span className={isDark ? 'text-gray-400' : 'text-gray-600'}>负值</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded border" style={{ backgroundColor: isDark ? '#1f2937' : '#f9fafb' }}></div>
          <span className={isDark ? 'text-gray-400' : 'text-gray-600'}>接近0</span>
        </div>
      </div>

      {/* 网格 */}
      <div
        className="grid gap-[2px] rounded-lg p-2 overflow-hidden"
        style={{
          gridTemplateColumns: `repeat(${cols}, 1fr)`,
          backgroundColor: isDark ? 'rgba(31, 41, 55, 0.5)' : 'rgba(249, 250, 251, 0.8)'
        }}
      >
        {cells.map(({ val, intensity }, i) => {
          const isPositive = val > 0
          const bgColor = isPositive
            ? `rgba(59, 130, 246, ${0.15 + intensity * 0.85})`
            : `rgba(239, 68, 68, ${0.15 + intensity * 0.85})`

          return (
            <motion.div
              key={i}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: i * 0.015, duration: 0.2 }}
              className="aspect-square rounded-sm flex items-center justify-center text-[8px] font-mono"
              style={{
                backgroundColor: bgColor,
                color: intensity > 0.5 ? 'white' : (isDark ? '#9ca3af' : '#6b7280')
              }}
              title={`[${i}]: ${val.toFixed(4)}`}
            >
              {val > 0 ? '+' : ''}{val.toFixed(2)}
            </motion.div>
          )
        })}
      </div>

      {/* 数值范围 */}
      <div className={`text-xs text-center ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
        值范围: [{Math.min(...showVector).toFixed(3)}, {Math.max(...showVector).toFixed(3)}] | 显示前{total}维，共{vector.length}维
      </div>
    </div>
  )
}

// 彩色热力图小方块
function VectorHeatmap({ vector, maxShow = 50, isDark = true }: { vector: number[], maxShow?: number, isDark?: boolean }) {
  const showVector = vector.slice(0, maxShow)
  return (
    <div className="flex flex-wrap gap-[2px]">
      {showVector.map((val, i) => (
        <motion.div
          key={i}
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: i * 0.01, duration: 0.2 }}
          className="w-3 h-3 rounded-sm"
          style={{
            backgroundColor: val > 0
              ? `rgba(59, 130, 246, ${Math.min(Math.abs(val) * 2, 1)})`
              : `rgba(239, 68, 68, ${Math.min(Math.abs(val) * 2, 1)})`
          }}
          title={val.toFixed(4)}
        />
      ))}
      {vector.length > maxShow && (
        <span className={`text-xs ml-1 self-center ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>...共{vector.length}维</span>
      )}
    </div>
  )
}

export default function StepVectorization({ chunks, vectors, queryVector, theme = 'dark' }: StepVectorizationProps) {
  const isDark = theme === 'dark'
  const [exampleVectors, setExampleVectors] = useState<{ v1: number[] | null, v2: number[] | null }[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 自定义文本对比
  const [customText1, setCustomText1] = useState('')
  const [customText2, setCustomText2] = useState('')
  const [customVectors, setCustomVectors] = useState<{ v1: number[] | null, v2: number[] | null }>({ v1: null, v2: null })
  const [customLoading, setCustomLoading] = useState(false)

  // 获取自定义文本的向量
  const fetchCustomVectors = async () => {
    if (!customText1.trim() || !customText2.trim()) return

    setCustomLoading(true)
    try {
      const response = await fetch('/api/rag/embed', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texts: [customText1, customText2] })
      })
      if (!response.ok) throw new Error('API error')
      const data = await response.json()
      setCustomVectors({ v1: data.embeddings[0], v2: data.embeddings[1] })
    } catch (err) {
      setCustomVectors({ v1: null, v2: null })
    } finally {
      setCustomLoading(false)
    }
  }

  // 计算 chunks 之间的相似度矩阵
  const similarityMatrix = useMemo(() => {
    const matrix: number[][] = []
    const allVectors = queryVector ? [...vectors, queryVector] : vectors
    const labels = queryVector
      ? [...chunks.map(c => c.id), 'query']
      : chunks.map(c => c.id)

    for (let i = 0; i < allVectors.length; i++) {
      const row: number[] = []
      for (let j = 0; j < allVectors.length; j++) {
        row.push(cosineSimilarity(allVectors[i], allVectors[j]))
      }
      matrix.push(row)
    }

    return { matrix, labels }
  }, [chunks, vectors, queryVector])

  // 获取示例的向量
  const fetchExampleVectors = async () => {
    setLoading(true)
    setError(null)

    try {
      const results = await Promise.all(
        EXAMPLES.map(async (ex) => {
          const response = await fetch('/api/rag/embed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ texts: [ex.text1, ex.text2] })
          })
          if (!response.ok) throw new Error('API error')
          const data = await response.json()
          return { v1: data.embeddings[0], v2: data.embeddings[1] }
        })
      )
      setExampleVectors(results)
    } catch (err) {
      setError('获取示例向量失败')
      // 使用零向量作为 fallback
      setExampleVectors(EXAMPLES.map(() => ({ v1: null, v2: null })))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-full flex flex-col gap-4 overflow-auto">
      <div className={`text-sm ${isDark ? 'text-dark-500' : 'text-gray-500'}`}>
        共 <span className="text-blue-400 font-bold">{chunks.length}</span> 个 chunks 向量化
      </div>

      {/* 自定义文本对比 */}
      <div className={`rounded-lg p-4 border ${isDark ? 'bg-dark-900 border-green-700/50' : 'bg-gray-50 border-green-300'}`}>
        <div className={`text-xs mb-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>自定义文本向量对比</div>
        <div className="flex gap-3 mb-3">
          <input
            type="text"
            value={customText1}
            onChange={(e) => setCustomText1(e.target.value)}
            placeholder="输入文本1..."
            className={`flex-1 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-green-500 ${isDark ? 'bg-dark-800 border border-dark-600 text-gray-200 placeholder-dark-500' : 'bg-white border border-gray-300 text-gray-800 placeholder-gray-400'}`}
          />
          <input
            type="text"
            value={customText2}
            onChange={(e) => setCustomText2(e.target.value)}
            placeholder="输入文本2..."
            className={`flex-1 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-green-500 ${isDark ? 'bg-dark-800 border border-dark-600 text-gray-200 placeholder-dark-500' : 'bg-white border border-gray-300 text-gray-800 placeholder-gray-400'}`}
          />
          <button
            onClick={fetchCustomVectors}
            disabled={customLoading || !customText1.trim() || !customText2.trim()}
            className="px-4 py-2 bg-green-600/20 text-green-400 rounded-lg text-sm hover:bg-green-600/30 disabled:opacity-50"
          >
            {customLoading ? '计算中...' : '计算相似度'}
          </button>
        </div>
        {customVectors.v1 && customVectors.v2 && (
          <div className={`flex items-center gap-4 mt-4 pt-4 border-t ${isDark ? 'border-dark-700' : 'border-gray-200'}`}>
            <div className="flex-1">
              <div className={`text-xs mb-1 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>文本1 向量</div>
              <div className={`text-sm mb-2 line-clamp-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{customText1}</div>
              <VectorHeatmap vector={customVectors.v1} maxShow={60} isDark={isDark} />
              <div className={`text-xs mt-1 ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>前60维 | 共{customVectors.v1.length}维</div>
            </div>
            <div className="text-center px-3">
              <div className="flex flex-col items-center">
                <div
                  className="w-20 h-20 rounded-lg flex items-center justify-center text-2xl font-bold"
                  style={{
                    backgroundColor: getHeatmapColor(cosineSimilarity(customVectors.v1, customVectors.v2)),
                    color: getTextColor(cosineSimilarity(customVectors.v1, customVectors.v2))
                  }}
                >
                  {cosineSimilarity(customVectors.v1, customVectors.v2).toFixed(2)}
                </div>
                <div className={`text-xs mt-1 ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>相似度</div>
              </div>
            </div>
            <div className="flex-1">
              <div className={`text-xs mb-1 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>文本2 向量</div>
              <div className={`text-sm mb-2 line-clamp-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{customText2}</div>
              <VectorHeatmap vector={customVectors.v2} maxShow={60} isDark={isDark} />
              <div className={`text-xs mt-1 ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>前60维 | 共{customVectors.v2.length}维</div>
            </div>
          </div>
        )}
      </div>

      {/* 固定示例对比 */}
      <div className={`rounded-lg p-4 border ${isDark ? 'bg-dark-900 border-dark-700' : 'bg-gray-50 border-gray-200'}`}>
        <div className="flex items-center justify-between mb-3">
          <div className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>固定示例文本向量对比</div>
          <button
            onClick={fetchExampleVectors}
            disabled={loading}
            className="px-2 py-1 text-xs bg-blue-600/20 text-blue-400 rounded hover:bg-blue-600/30 disabled:opacity-50"
          >
            {loading ? '加载中...' : '获取向量'}
          </button>
        </div>

        {error && <div className={`text-xs mb-2 ${isDark ? 'text-red-400' : 'text-red-500'}`}>{error}</div>}

        <div className="space-y-4">
          {EXAMPLES.map((ex, idx) => {
            const vecs = exampleVectors[idx] || { v1: null, v2: null }
            const sim = vecs.v1 && vecs.v2 ? cosineSimilarity(vecs.v1, vecs.v2) : null

            return (
              <div key={idx} className={`border rounded-lg p-4 ${isDark ? 'border-dark-700' : 'border-gray-200'}`}>
                <div className="flex items-center gap-2 mb-3">
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    ex.color === 'blue' ? 'bg-blue-600/20 text-blue-400' :
                    ex.color === 'yellow' ? 'bg-yellow-600/20 text-yellow-400' :
                    'bg-red-600/20 text-red-400'
                  }`}>
                    {ex.label}
                  </span>
                  <span className={`text-xs ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>点击"获取向量"查看真实向量</span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <div className={`text-xs mb-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>文本1 向量 (2048维)</div>
                    <div className={`text-sm mb-2 line-clamp-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{ex.text1}</div>
                    {vecs.v1 ? (
                      <div>
                        <VectorHeatmap vector={vecs.v1} maxShow={60} isDark={isDark} />
                        <div className={`text-xs mt-1 ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>前60维 | 共{vecs.v1.length}维</div>
                      </div>
                    ) : (
                      <div className={`text-xs py-4 ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>点击"获取向量"</div>
                    )}
                  </div>
                  <div className="text-center px-3">
                    {vecs.v1 && vecs.v2 ? (
                      <div className="flex flex-col items-center">
                        <div
                          className="w-16 h-16 rounded-lg flex items-center justify-center text-xl font-bold"
                          style={{
                            backgroundColor: getHeatmapColor(sim || 0),
                            color: getTextColor(sim || 0)
                          }}
                        >
                          {(sim || 0).toFixed(2)}
                        </div>
                        <div className={`text-xs mt-1 ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>相似度</div>
                      </div>
                    ) : (
                      <div className={`w-16 h-16 rounded-lg border flex items-center justify-center text-xs ${isDark ? 'border-dark-600 text-dark-500' : 'border-gray-300 text-gray-400'}`}>
                        相似度
                      </div>
                    )}
                  </div>
                  <div className="flex-1">
                    <div className={`text-xs mb-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>文本2 向量 (2048维)</div>
                    <div className={`text-sm mb-2 line-clamp-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{ex.text2}</div>
                    {vecs.v2 ? (
                      <div>
                        <VectorHeatmap vector={vecs.v2} maxShow={60} isDark={isDark} />
                        <div className={`text-xs mt-1 ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>前60维 | 共{vecs.v2.length}维</div>
                      </div>
                    ) : (
                      <div className={`text-xs py-4 ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>点击"获取向量"</div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Chunk 向量可视化条 */}
      <div className={`rounded-lg p-4 border ${isDark ? 'bg-dark-900 border-dark-700' : 'bg-gray-50 border-gray-200'}`}>
        <div className={`text-xs mb-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Chunk 向量可视化
          <span className={`ml-2 ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>（条形高度表示值大小，正值蓝色，负值红色）</span>
        </div>
        <div className="grid grid-cols-2 gap-4">
          {chunks.slice(0, 4).map((chunk, index) => {
            const vector = vectors[index] || []
            return (
              <motion.div
                key={chunk.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`rounded-lg p-3 border ${isDark ? 'border-dark-700 bg-dark-800/50' : 'border-gray-200 bg-white/50'}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-xs font-mono px-2 py-1 rounded ${isDark ? 'text-blue-400 bg-blue-400/10' : 'text-blue-600 bg-blue-50'}`}>
                    {chunk.id}
                  </span>
                  <span className={`text-xs ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>{vector.length}维</span>
                </div>
                <VectorGrid vector={vector} isDark={isDark} rows={4} cols={8} />
              </motion.div>
            )
          })}
        </div>
        {chunks.length > 4 && (
          <div className={`text-xs text-center mt-3 ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>
            还有 {chunks.length - 4} 个 chunk...
          </div>
        )}
      </div>

      {/* 相似度矩阵热力图 */}
      <div>
        <div className={`text-xs mb-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>完整相似度矩阵</div>
        <div className="overflow-auto">
          <table className="border-collapse">
            <thead>
              <tr>
                <th className={`p-1 text-xs ${isDark ? 'text-dark-500' : 'text-gray-400'}`}></th>
                {similarityMatrix.labels.map((label, i) => (
                  <th key={i} className={`p-1 text-xs font-mono min-w-[60px] ${isDark ? 'text-blue-400' : 'text-blue-600'}`}>
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {similarityMatrix.matrix.map((row, i) => (
                <tr key={i}>
                  <td className={`p-1 text-xs font-mono ${isDark ? 'text-blue-400' : 'text-blue-600'}`}>{similarityMatrix.labels[i]}</td>
                  {row.map((val, j) => (
                    <td key={j} className="p-1 text-center">
                      <div
                        className="w-12 h-8 rounded flex items-center justify-center text-xs font-mono"
                        style={{
                          backgroundColor: getHeatmapColor(val),
                          color: getTextColor(val)
                        }}
                        title={`${similarityMatrix.labels[i]} vs ${similarityMatrix.labels[j]}: ${val.toFixed(3)}`}
                      >
                        {val.toFixed(2)}
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className={`flex items-center gap-4 mt-2 text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
          <div className="flex items-center gap-1">
            <div className="w-4 h-3 rounded" style={{ backgroundColor: 'rgba(59, 130, 246, 0.2)' }}></div>
            <span>低</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-3 rounded" style={{ backgroundColor: 'rgba(59, 130, 246, 0.9)' }}></div>
            <span>高</span>
          </div>
        </div>
      </div>

      {/* 向量详情折叠 */}
      <div className="space-y-2">
        <div className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>向量详情 (点击展开)</div>
        {chunks.map((chunk, index) => {
          const vector = vectors[index] || []
          const dim = vector.length

          return (
            <details
              key={chunk.id}
              className={`rounded-lg border group ${isDark ? 'bg-dark-900 border-dark-700' : 'bg-gray-50 border-gray-200'}`}
            >
              <summary className={`flex items-center justify-between p-3 cursor-pointer list-none hover:${isDark ? 'bg-dark-800' : 'bg-gray-100'}`}>
                <div className="flex items-center gap-3">
                  <span className={`text-xs font-mono px-2 py-1 rounded ${isDark ? 'text-blue-400 bg-blue-400/10' : 'text-blue-600 bg-blue-50'}`}>
                    {chunk.id}
                  </span>
                  <span className={`text-xs ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>{dim}维向量</span>
                </div>
                <svg
                  className={`w-4 h-4 transition-transform ${isDark ? 'text-dark-500' : 'text-gray-400'}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </summary>
              <div className="px-3 pb-3">
                <div className={`text-xs mb-2 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
                  向量前20维: [{vector.slice(0, 20).map(v => v.toFixed(3)).join(', ')}...]
                </div>
              </div>
            </details>
          )
        })}
      </div>
    </div>
  )
}
