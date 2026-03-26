import { ProcessRequest, RagProcessResult } from '../App'
import { STEPS } from '../App'

interface ExplanationPanelProps {
  currentStep: number
  inputData: ProcessRequest
  result: RagProcessResult | null
  theme?: 'dark' | 'light'
}

const EXPLANATIONS: Record<number, { title: string; content: string }> = {
  1: {
    title: '原始文本',
    content: `RAG 的起点是知识文本，而不是模型直接"知道答案"。

这里展示的是将要进入 RAG 流程的原始文档内容。通常来自知识库、文档库或数据库。

关键点：
• 文档可能包含噪声（多余空格、特殊符号）
• 文档结构可能不统一
• 需要后续处理才能被模型有效利用`
  },
  2: {
    title: '预处理',
    content: `文档不能直接拿去切片，通常需要预处理。

常见预处理操作：
• 去除多余空格和换行
• 清除无意义的符号
• 统一文本格式
• 结构化段落划分
• 增加元数据标记

预处理的目标是让文本更加干净、规范，为后续切片做准备。`
  },
  3: {
    title: '切片（Chunking）',
    content: `为什么要切片？
• 大模型有上下文长度限制
• 完整的文档太长，难以精确匹配
• 适当的 chunk 大小能提高检索精度

关键参数：
• Chunk Size：每个 chunk 的词数（当前: ${50}词）
• Overlap：相邻 chunk 之间的重叠词数（增加上下文连贯性）

切片策略：
• 按字数：简单直接，但可能在句子中间断开
• 按句子：更自然，但大小不均匀
• 按段落：保持语义完整性，但大小不一`
  },
  4: {
    title: '向量化',
    content: `文本被编码成语义向量，后续才能进行相似度检索。

向量化的本质：
• 将文本映射到高维向量空间
• 语义相似的文本在向量空间中距离更近
• 可以通过余弦相似度等度量计算相关性

本演示使用简化的高维向量表示：
• 实际生产中通常使用 OpenAI embedding、Sentence-BERT 等模型
• 向量维度通常在 768-1536 之间
• 这里简化为 10 维便于可视化`
  },
  5: {
    title: '用户提问',
    content: `RAG 的入口不仅是文档，也包括用户问题。

Query 的重要性：
• 用户的提问决定了检索的方向
• Query 本身也需要向量化
• Query 与 chunks 在同一向量空间中进行匹配

Query 处理特点：
• 通常比文档片段更短
• 可能包含口语化表达
• 需要理解用户真实意图`
  },
  6: {
    title: '相似度检索',
    content: `RAG 主要依赖语义检索，而不是简单关键词匹配。

检索过程：
1. 将 Query 向量化
2. 计算 Query 与所有 chunks 的相似度
3. 召回 Top-K 个最相关的结果

相似度度量方式：
• 余弦相似度（Cosine Similarity）
• 点积（Dot Product）
• 欧氏距离（Euclidean Distance）

本演示使用余弦相似度，值范围 0-1，越接近 1 表示越相似。`
  },
  7: {
    title: '重排（Rerank）',
    content: `向量召回解决"找相关"，重排解决"找最适合回答的"。

为什么需要重排？
• 向量检索可能遗漏语义细节
• 有些 chunk 与问题表面相似但实际不相关
• 重排模型能更好地理解 Query 和 Document 的匹配度

重排的作用：
• 更精细的相关性评估
• 可能改变初始排序
• 提高最终答案的质量

当前配置：${true ? '启用' : '未启用'}重排`
  },
  8: {
    title: 'Prompt 组装',
    content: `模型真正看到的是一个拼装后的 Prompt，不只是用户问题本身。

Prompt 组成：
• System Prompt：设定模型角色和回答规则
• Context：检索到的相关文档片段
• User Query：用户的原始问题

组装原则：
• Context 要精选，不是越多越好
• 需要明确指示模型基于上下文回答
• 如果上下文不足，需要模型承认不知道`

  },
  9: {
    title: '答案生成',
    content: `模型的回答是建立在检索到的上下文之上的。

答案生成要点：
• 基于检索到的上下文进行回答
• 如果上下文不相关，答案也会不准确
• 可以引用具体来源增加可信度

RAG 的优势：
• 答案基于真实数据，更可靠
• 可以追溯到具体来源
• 比纯生成更不易产生幻觉

这是 RAG 流程的最终输出！`
  }
}

export default function ExplanationPanel({ currentStep, inputData, result, theme = 'dark' }: ExplanationPanelProps) {
  const isDark = theme === 'dark'
  const explanation = EXPLANATIONS[currentStep] || { title: '', content: '' }

  return (
    <div className={`rounded-xl p-4 h-full flex flex-col ${isDark ? 'bg-dark-800' : 'bg-white border border-gray-200'}`}>
      <h2 className={`text-lg font-semibold border-b pb-2 mb-4 ${isDark ? 'text-white border-dark-700' : 'text-gray-900 border-gray-200'}`}>
        步骤 {currentStep}: {explanation.title}
      </h2>
      <div className="flex-1 overflow-auto">
        <div className={`prose prose-sm max-w-none ${!isDark ? 'prose-gray' : ''}`}>
          <pre className={`whitespace-pre-wrap text-sm font-sans p-4 rounded-lg ${isDark ? 'text-gray-300 bg-dark-900' : 'text-gray-700 bg-gray-50'}`}>
            {explanation.content.replace('${50}', String(inputData.chunk_size)).replace('${10}', String(inputData.overlap)).replace('${true}', String(inputData.use_rerank))}
          </pre>
        </div>

        {/* Step progress indicator */}
        <div className={`mt-4 pt-4 border-t ${isDark ? 'border-dark-700' : 'border-gray-200'}`}>
          <div className={`text-xs mb-2 ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>演示进度</div>
          <div className="flex gap-1">
            {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((step) => (
              <div
                key={step}
                className={`h-2 flex-1 rounded ${
                  step <= currentStep ? 'bg-blue-600' : isDark ? 'bg-dark-700' : 'bg-gray-200'
                }`}
              />
            ))}
          </div>
          <div className={`text-xs mt-1 ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>
            {currentStep} / 9 步骤完成
          </div>
        </div>
      </div>
    </div>
  )
}
