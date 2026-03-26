import { useMemo } from 'react'
import { motion } from 'framer-motion'

interface StepPreprocessingProps {
  original: string
  preprocessed: string
  theme?: 'dark' | 'light'
}

export default function StepPreprocessing({ original, preprocessed, theme = 'dark' }: StepPreprocessingProps) {
  const isDark = theme === 'dark'

  // 计算差异
  const diffs = useMemo(() => {
    const result: { type: 'same' | 'removed' | 'added'; text: string }[] = []
    const origChars = original.split('')
    const prepChars = preprocessed.split('')

    let i = 0, j = 0
    while (i < origChars.length || j < prepChars.length) {
      if (i >= origChars.length) {
        // 预处理后新增的
        result.push({ type: 'added', text: prepChars.slice(j).join('') })
        break
      }
      if (j >= prepChars.length) {
        // 原始中删除的
        result.push({ type: 'removed', text: origChars.slice(i).join('') })
        break
      }
      if (origChars[i] === prepChars[j]) {
        // 相同
        let same = ''
        while (i < origChars.length && j < prepChars.length && origChars[i] === prepChars[j]) {
          same += origChars[i]
          i++
          j++
        }
        result.push({ type: 'same', text: same })
      } else {
        // 不匹配，检查是删除还是新增
        // 简单策略：优先处理连续删除/新增
        let removed = ''
        let added = ''

        // 向前看，看是否是删除
        const origLookAhead = origChars.slice(i, i + 3).join('')
        const prepLookAhead = prepChars.slice(j, j + 3).join('')

        if (origLookAhead.includes(prepChars[j]) || !prepChars[j].match(/\s/)) {
          removed += origChars[i]
          i++
        }
        if (j < prepChars.length && (prepLookAhead.includes(origChars[i]) || !origChars[i]?.match(/\s/))) {
          added += prepChars[j]
          j++
        } else if (i < origChars.length && removed === '') {
          removed += origChars[i]
          i++
        }

        if (removed) result.push({ type: 'removed', text: removed })
        if (added) result.push({ type: 'added', text: added })
      }
    }

    return result
  }, [original, preprocessed])

  return (
    <div className="h-full flex flex-col gap-4">
      {/* 统计信息 */}
      <div className="flex gap-4 text-xs">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`px-3 py-2 rounded-lg ${isDark ? 'bg-red-400/10 border border-red-400/30' : 'bg-red-50 border border-red-200'}`}
        >
          <span className="text-red-400">删除 </span>
          <span className="font-bold">{original.length - preprocessed.length}</span>
          <span className={isDark ? 'text-dark-500' : 'text-gray-400'}> 字符</span>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className={`px-3 py-2 rounded-lg ${isDark ? 'bg-dark-800' : 'bg-gray-100'}`}
        >
          <span className={isDark ? 'text-dark-400' : 'text-gray-600'}>
            {original.length} → {preprocessed.length} 字符
          </span>
        </motion.div>
      </div>

      {/* 差异对比视图 */}
      <div className={`flex-1 rounded-lg p-4 ${isDark ? 'bg-dark-900' : 'bg-gray-50 border border-gray-200'}`}>
        <div className={`text-xs mb-3 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
          差异高亮视图
        </div>
        <div className="h-32 overflow-auto">
          <div className="flex flex-wrap items-start gap-1 text-sm leading-relaxed font-sans">
            {diffs.map((diff, idx) => {
              if (diff.type === 'same') {
                return (
                  <span key={idx} className={isDark ? 'text-gray-300' : 'text-gray-800'}>
                    {diff.text}
                  </span>
                )
              } else if (diff.type === 'removed') {
                return (
                  <motion.span
                    key={idx}
                    initial={{ backgroundColor: 'rgba(239, 68, 68, 0.5)' }}
                    animate={{ backgroundColor: 'rgba(239, 68, 68, 0.2)' }}
                    className="text-red-400 line-through rounded px-0.5"
                  >
                    {diff.text}
                  </motion.span>
                )
              } else {
                return (
                  <motion.span
                    key={idx}
                    initial={{ backgroundColor: 'rgba(34, 197, 94, 0.5)' }}
                    animate={{ backgroundColor: 'rgba(34, 197, 94, 0.2)' }}
                    className="text-green-400 rounded px-0.5"
                  >
                    {diff.text}
                  </motion.span>
                )
              }
            })}
          </div>
        </div>
      </div>

      {/* Before/After 并排视图 */}
      <div className="flex gap-4 flex-1">
        {/* Before */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className={`flex-1 rounded-lg p-4 ${isDark ? 'bg-dark-900' : 'bg-gray-50 border border-gray-200'}`}
        >
          <div className={`flex items-center justify-between mb-3 ${isDark ? 'text-dark-500' : 'text-gray-500'}`}>
            <span className="text-sm text-red-400">处理前</span>
            <span className={`text-xs ${isDark ? 'text-dark-600' : 'text-gray-400'}`}>{original.length} 字符</span>
          </div>
          <pre className={`whitespace-pre-wrap text-sm leading-relaxed font-sans h-32 overflow-auto ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            {original}
          </pre>
        </motion.div>

        {/* Arrow */}
        <div className="flex items-center">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2 }}
            className="w-12 h-12 bg-blue-600/20 rounded-full flex items-center justify-center"
          >
            <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </motion.div>
        </div>

        {/* After */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className={`flex-1 rounded-lg p-4 ${isDark ? 'bg-dark-900' : 'bg-gray-50 border border-gray-200'}`}
        >
          <div className={`flex items-center justify-between mb-3 ${isDark ? 'text-dark-500' : 'text-gray-500'}`}>
            <span className="text-sm text-green-400">处理后</span>
            <span className={`text-xs ${isDark ? 'text-dark-600' : 'text-gray-400'}`}>{preprocessed.length} 字符</span>
          </div>
          <pre className={`whitespace-pre-wrap text-sm leading-relaxed font-sans h-32 overflow-auto ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
            {preprocessed}
          </pre>
        </motion.div>
      </div>
    </div>
  )
}
