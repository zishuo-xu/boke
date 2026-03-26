import { useMemo } from 'react'
import { motion } from 'framer-motion'

interface StepPromptProps {
  prompt: string
  theme?: 'dark' | 'light'
}

export default function StepPrompt({ prompt, theme = 'dark' }: StepPromptProps) {
  const isDark = theme === 'dark'

  // 解析 Prompt 结构
  const parsedPrompt = useMemo(() => {
    // 匹配系统提示（到"上下文信息"之前）
    const systemMatch = prompt.match(/^(.*?)(?=\n\n上下文信息:)/s)
    const contextMatch = prompt.match(/(?:\n\n上下文信息:\n)([\s\S]*?)(?=\n\n用户问题:)/)
    const queryMatch = prompt.match(/(?:\n\n用户问题:)([\s\S]*?)$/)

    return {
      system: systemMatch?.[1]?.trim() || '',
      context: contextMatch?.[1]?.trim() || '',
      query: queryMatch?.[1]?.trim() || ''
    }
  }, [prompt])

  // 计算各部分长度
  const systemLen = parsedPrompt.system.length
  const contextLen = parsedPrompt.context.length
  const queryLen = parsedPrompt.query.length

  return (
    <div className="h-full flex flex-col gap-4">
      {/* 统计信息 */}
      <div className="flex gap-3 text-xs">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`px-3 py-2 rounded-lg ${isDark ? 'bg-blue-500/10 border border-blue-500/30' : 'bg-blue-50 border border-blue-200'}`}
        >
          <span className="text-blue-400 font-medium">系统提示 </span>
          <span className="font-bold text-blue-300">{systemLen}</span>
          <span className={isDark ? 'text-dark-500' : 'text-gray-400'}> 字符</span>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className={`px-3 py-2 rounded-lg ${isDark ? 'bg-green-500/10 border border-green-500/30' : 'bg-green-50 border border-green-200'}`}
        >
          <span className="text-green-400 font-medium">上下文 </span>
          <span className="font-bold text-green-300">{contextLen}</span>
          <span className={isDark ? 'text-dark-500' : 'text-gray-400'}> 字符</span>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className={`px-3 py-2 rounded-lg ${isDark ? 'bg-yellow-500/10 border border-yellow-500/30' : 'bg-yellow-50 border border-yellow-200'}`}
        >
          <span className="text-yellow-400 font-medium">用户问题 </span>
          <span className="font-bold text-yellow-300">{queryLen}</span>
          <span className={isDark ? 'text-dark-500' : 'text-gray-400'}> 字符</span>
        </motion.div>
      </div>

      {/* Prompt 结构可视化 */}
      <div className={`rounded-lg p-4 ${isDark ? 'bg-dark-900' : 'bg-gray-50 border border-gray-200'}`}>
        <div className={`text-xs mb-3 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
          Prompt 结构分解
        </div>

        <div className="space-y-3">
          {/* System Prompt */}
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className={`rounded-lg p-3 border ${isDark ? 'bg-blue-500/5 border-blue-500/30' : 'bg-blue-50 border-blue-200'}`}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-500/20 text-blue-400">System</span>
              <span className={`text-xs ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>系统指令，定义 AI 角色</span>
            </div>
            <pre className={`whitespace-pre-wrap text-sm leading-relaxed ${isDark ? 'text-blue-300' : 'text-blue-700'}`}>
              {parsedPrompt.system}
            </pre>
          </motion.div>

          {/* Context */}
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className={`rounded-lg p-3 border ${isDark ? 'bg-green-500/5 border-green-500/30' : 'bg-green-50 border-green-200'}`}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-0.5 rounded text-xs font-medium bg-green-500/20 text-green-400">Context</span>
              <span className={`text-xs ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>检索召回的文档片段</span>
            </div>
            <pre className={`whitespace-pre-wrap text-sm leading-relaxed ${isDark ? 'text-green-300' : 'text-green-700'}`}>
              {parsedPrompt.context}
            </pre>
          </motion.div>

          {/* Query */}
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className={`rounded-lg p-3 border ${isDark ? 'bg-yellow-500/5 border-yellow-500/30' : 'bg-yellow-50 border-yellow-200'}`}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-0.5 rounded text-xs font-medium bg-yellow-500/20 text-yellow-400">Query</span>
              <span className={`text-xs ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>用户输入的问题</span>
            </div>
            <pre className={`whitespace-pre-wrap text-sm leading-relaxed ${isDark ? 'text-yellow-300' : 'text-yellow-700'}`}>
              {parsedPrompt.query}
            </pre>
          </motion.div>
        </div>
      </div>

      {/* 原始 Prompt */}
      <div className={`rounded-lg p-4 border ${isDark ? 'bg-dark-900 border-dark-700' : 'bg-gray-50 border-gray-200'}`}>
        <div className={`flex items-center justify-between mb-3 ${isDark ? 'text-dark-500' : 'text-gray-500'}`}>
          <span className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>完整 Prompt（原始）</span>
          <span className={`text-xs ${isDark ? 'text-dark-600' : 'text-gray-400'}`}>{prompt.length} 字符</span>
        </div>
        <pre className={`whitespace-pre-wrap text-sm font-mono leading-relaxed max-h-48 overflow-auto ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          {prompt}
        </pre>
      </div>
    </div>
  )
}
