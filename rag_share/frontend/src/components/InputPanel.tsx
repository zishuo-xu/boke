import { ProcessRequest } from '../App'

interface InputPanelProps {
  inputData: ProcessRequest
  setInputData: (data: ProcessRequest) => void
  onProcess: () => void
  isProcessing: boolean
  hasResult: boolean
  theme?: 'dark' | 'light'
}

export default function InputPanel({
  inputData,
  setInputData,
  onProcess,
  isProcessing,
  hasResult,
  theme = 'dark'
}: InputPanelProps) {
  const isDark = theme === 'dark'

  return (
    <div className={`rounded-xl p-4 h-full flex flex-col gap-4 ${isDark ? 'bg-dark-800' : 'bg-white border border-gray-200'}`}>
      <h2 className={`text-lg font-semibold border-b pb-2 ${isDark ? 'text-white border-dark-700' : 'text-gray-900 border-gray-200'}`}>输入配置</h2>

      {/* Original Text */}
      <div>
        <label className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>原始文本</label>
        <textarea
          value={inputData.text}
          onChange={(e) => setInputData({ ...inputData, text: e.target.value })}
          className={`w-full h-32 rounded-lg p-3 text-sm resize-none focus:outline-none focus:border-blue-500 ${isDark ? 'bg-dark-900 border-dark-700 text-gray-200' : 'bg-gray-50 border-gray-300 text-gray-900'}`}
          placeholder="输入知识库文本..."
        />
      </div>

      {/* Query */}
      <div>
        <label className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>用户问题</label>
        <input
          type="text"
          value={inputData.query}
          onChange={(e) => setInputData({ ...inputData, query: e.target.value })}
          className={`w-full rounded-lg p-3 text-sm focus:outline-none focus:border-blue-500 ${isDark ? 'bg-dark-900 border-dark-700 text-gray-200' : 'bg-gray-50 border-gray-300 text-gray-900'}`}
          placeholder="输入查询问题..."
        />
      </div>

      {/* Parameters */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Chunk Size</label>
          <input
            type="number"
            value={inputData.chunk_size}
            onChange={(e) => setInputData({ ...inputData, chunk_size: parseInt(e.target.value) || 50 })}
            className={`w-full rounded-lg p-2 text-sm focus:outline-none focus:border-blue-500 ${isDark ? 'bg-dark-900 border-dark-700 text-gray-200' : 'bg-gray-50 border-gray-300 text-gray-900'}`}
          />
        </div>
        <div>
          <label className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Overlap</label>
          <input
            type="number"
            value={inputData.overlap}
            onChange={(e) => setInputData({ ...inputData, overlap: parseInt(e.target.value) || 10 })}
            className={`w-full rounded-lg p-2 text-sm focus:outline-none focus:border-blue-500 ${isDark ? 'bg-dark-900 border-dark-700 text-gray-200' : 'bg-gray-50 border-gray-300 text-gray-900'}`}
          />
        </div>
        <div>
          <label className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Top K</label>
          <input
            type="number"
            value={inputData.top_k}
            onChange={(e) => setInputData({ ...inputData, top_k: parseInt(e.target.value) || 3 })}
            className={`w-full rounded-lg p-2 text-sm focus:outline-none focus:border-blue-500 ${isDark ? 'bg-dark-900 border-dark-700 text-gray-200' : 'bg-gray-50 border-gray-300 text-gray-900'}`}
          />
        </div>
        <div>
          <label className={`block text-sm font-medium mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>切片方式</label>
          <select
            value={inputData.chunking_strategy}
            onChange={(e) => setInputData({ ...inputData, chunking_strategy: e.target.value })}
            className={`w-full rounded-lg p-2 text-sm focus:outline-none focus:border-blue-500 ${isDark ? 'bg-dark-900 border-dark-700 text-gray-200' : 'bg-gray-50 border-gray-300 text-gray-900'}`}
          >
            <option value="by_chars">按字符</option>
            <option value="by_sentence">按句子</option>
            <option value="by_paragraph">按段落</option>
          </select>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={inputData.use_rerank}
            onChange={(e) => setInputData({ ...inputData, use_rerank: e.target.checked })}
            className="w-4 h-4 rounded border-dark-600 bg-dark-900 text-blue-600 focus:ring-blue-500"
          />
          <span className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>启用重排</span>
        </label>
      </div>

      {/* PostgreSQL 模式选择 */}
      <div className={`border-t pt-4 ${isDark ? 'border-dark-700' : 'border-gray-200'}`}>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={inputData.use_pg}
            onChange={(e) => setInputData({ ...inputData, use_pg: e.target.checked })}
            className="w-4 h-4 rounded border-dark-600 bg-dark-900 text-blue-600 focus:ring-blue-500"
          />
          <span className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            使用 PostgreSQL 混合检索
          </span>
        </label>
        <div className={`mt-1 text-xs ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>
          {inputData.use_pg
            ? '模式：向量检索 + 关键词检索 + RRF 融合'
            : '模式：内存向量检索'}
        </div>
      </div>

      {/* Process Button */}
      <button
        onClick={onProcess}
        disabled={isProcessing || !inputData.text || !inputData.query}
        className={`
          w-full py-3 rounded-lg font-medium transition-all
          ${isProcessing
            ? isDark ? 'bg-dark-700 text-dark-500' : 'bg-gray-200 text-gray-400'
            : 'bg-blue-600 text-white hover:bg-blue-500 shadow-lg shadow-blue-600/30'
          }
        `}
      >
        {isProcessing ? '处理中...' : hasResult ? '重新开始演示' : '开始演示'}
      </button>

      {/* Quick Fill */}
      <button
        onClick={() => setInputData({
          text: `智能客服系统用户手册

第一章：系统概述

智能客服系统是一套基于人工智能技术的在线客户服务解决方案，旨在为企业提供高效、准确、7×24小时在线的客户支持服务。本系统整合了自然语言处理、机器学习、知识图谱等多项先进技术，能够理解用户意图并提供精准的答案。

系统主要功能包括：智能问答自动回复、多轮对话管理、意图识别、情感分析、问题转人工、知识库管理、数据统计分析等。通过这些功能，企业可以显著降低客服成本，同时提升客户满意度和服务效率。

第二章：系统架构

本系统采用微服务架构设计，主要包含以下核心模块：

自然语言理解模块负责对用户输入进行分词、词性标注、命名实体识别等预处理操作，提取出文本中的关键信息和语义特征。该模块基于深度学习模型构建，经过大量语料训练，能够准确理解各种表达方式的用户query。

对话管理模块控制对话流程，维护对话状态，支持多轮对话场景。当用户提出复杂问题时，系统能够通过多轮交互逐步澄清用户需求，最终给出准确答案。该模块还负责对话策略的选择，决定何时调用知识库检索、何时转人工服务。

知识库检索模块是系统的核心组件，基于RAG（检索增强生成）架构构建。当用户提出问题时，系统首先在知识库中检索相关内容，然后结合检索结果生成答案。知识库支持多种格式的内容导入，包括FAQ文档、产品手册、操作指南等。

答案生成模块负责将检索到的内容和用户问题组合成完整的回答。系统使用大语言模型进行答案生成，能够生成流畅、自然的回复，同时确保答案基于知识库中的真实内容。

第三章：知识库管理

知识库是智能客服系统的基础，高质量的知识库是系统良好运行的前提。知识库管理功能包括知识的创建、编辑、审核、发布全流程管理。

知识条目由问题和答案组成，支持富文本格式。管理员可以为知识条目设置分类标签、关键词、相似问法等属性，提高检索召回率。系统还支持知识条目的批量导入和导出，方便与企业现有知识库对接。

知识库的维护需要持续进行。管理员应定期审查知识库内容，更新老旧信息，补充新常见问题。系统提供数据分析功能，可以统计各知识条目的访问频率、满意度评分等指标，帮助管理员识别需要优先优化的内容。

第四章：对话配置

对话配置影响系统的对话行为和交互体验。主要配置项包括：

欢迎语配置定义用户首次访问时看到的问候信息，好的欢迎语应该简洁明了，告知用户可以提供什么帮助。

意图识别配置定义系统需要识别的用户意图类型，如咨询、投诉、建议、闲聊等。不同意图可以触发不同的处理流程。

转人工规则配置定义何时应该将对话转接到人工客服。常见转人工条件包括：用户明确要求转人工、问题多次未能解决、用户情绪负面、涉及敏感操作等。

答案生成配置影响回复的风格和格式。可以配置回复的最大长度、是否显示信息来源、是否使用表情符号等。

第五章：数据统计

系统提供完善的数据统计分析功能，帮助企业了解客服运营状况。

对话统计包括每日对话量、对话时长、解决的问题数、解决率等核心指标。这些数据可以帮助企业评估客服工作效率和系统使用情况。

用户反馈统计收集用户对每次回复的满意度评价，包括满意、一般、不满意三个等级。不满意评价应重点分析原因，针对性优化知识库或系统配置。

热点问题分析自动统计高频访问的问题，帮助企业了解用户关注的焦点。这些热点问题应该是知识库建设的优先内容。

第六章：系统集成

智能客服系统支持多种集成方式，方便与企业现有系统对接。

API集成提供RESTful接口，允许企业系统通过HTTP请求调用客服功能。可以将智能客服嵌入网站、移动APP、微信公众号等多种渠道。

SDK集成提供客户端开发包，支持iOS、Android、小程序等平台的原生开发，实现更深度定制和更好的用户体验。

第三方系统对接支持与企业CRM、工单系统、知识库系统等对接，实现数据互通和流程协同。

第七章：使用注意事项

为保证系统稳定运行和服务质量，请注意以下事项：

知识库内容应该准确、规范，避免模糊或歧义性表述。同一问题应有统一的答案格式，便于系统学习和用户理解。

定期检查系统日志和统计数据，及时发现和处理异常情况。对于系统无法解决的问题，应及时补充相关知识条目。

敏感信息和隐私数据不应添加到知识库中，如涉及此类问题应及时转人工处理。

系统升级维护应选择在业务低峰期进行，提前通知用户并做好回滚准备。`,
          query: '如何将客服系统集成到APP中？',
          chunk_size: 150,
          overlap: 30,
          top_k: 3,
          use_rerank: true,
          chunking_strategy: 'by_chars',
          use_pg: false,
          use_pg: false
        })}
        className={`text-sm ${isDark ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-700'} underline`}
      >
        填充示例内容
      </button>
    </div>
  )
}
