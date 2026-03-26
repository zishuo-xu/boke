import { useState } from 'react'
import { Chunk } from '../../App'

interface StepChunkingProps {
  chunks: Chunk[]
  editedChunks: Chunk[] | null
  onChunksChange: (chunks: Chunk[] | null) => void
  theme?: 'dark' | 'light'
}

export default function StepChunking({ chunks, editedChunks, onChunksChange, theme = 'dark' }: StepChunkingProps) {
  const isDark = theme === 'dark'
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editText, setEditText] = useState('')

  // 使用编辑后的 chunks 或原始 chunks
  const displayChunks = editedChunks || chunks

  const startEdit = (chunk: Chunk) => {
    setEditingId(chunk.id)
    setEditText(chunk.text)
  }

  const saveEdit = (chunkId: string) => {
    if (!editedChunks) {
      // 第一次编辑，创建编辑后的副本
      const newChunks = displayChunks.map(c =>
        c.id === chunkId ? { ...c, text: editText, length: editText.length } : c
      )
      onChunksChange(newChunks)
    } else {
      // 后续编辑直接更新
      const newChunks = editedChunks.map(c =>
        c.id === chunkId ? { ...c, text: editText, length: editText.length } : c
      )
      onChunksChange(newChunks)
    }
    setEditingId(null)
    setEditText('')
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditText('')
  }

  const deleteChunk = (chunkId: string) => {
    const newChunks = displayChunks.filter(c => c.id !== chunkId)
    onChunksChange(newChunks.length === chunks.length ? null : newChunks)
  }

  const addChunk = () => {
    const newId = `chunk_${displayChunks.length}`
    const newChunk: Chunk = {
      id: newId,
      text: '',
      length: 0
    }
    const newChunks = [...displayChunks, newChunk]
    onChunksChange(newChunks)
    // 自动开始编辑新chunk
    setEditingId(newId)
    setEditText('')
  }

  const resetToOriginal = () => {
    onChunksChange(null)
  }

  return (
    <div className="h-full flex flex-col">
      <div className={`text-sm mb-4 ${isDark ? 'text-dark-500' : 'text-gray-500'}`}>
        共 <span className="text-blue-400 font-bold">{displayChunks.length}</span> 个 chunks，支持编辑、新增、删除
      </div>

      <div className="mb-4 flex gap-2">
        <button
          onClick={addChunk}
          className="px-3 py-1.5 bg-blue-600/20 text-blue-400 rounded-lg text-sm hover:bg-blue-600/30 transition-colors"
        >
          + 新增切片
        </button>
        {editedChunks && (
          <button
            onClick={resetToOriginal}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${isDark ? 'bg-dark-700 text-gray-400 hover:bg-dark-600' : 'bg-gray-200 text-gray-600 hover:bg-gray-300'}`}
          >
            重置为原始
          </button>
        )}
      </div>

      <div className="flex-1 overflow-auto space-y-3">
        {displayChunks.map((chunk, index) => (
          <div
            key={chunk.id}
            className={`rounded-lg border p-3 ${isDark ? 'bg-dark-900 border-dark-700' : 'bg-gray-50 border-gray-200'}`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className={`text-xs font-mono px-2 py-1 rounded ${isDark ? 'text-blue-400 bg-blue-400/10' : 'text-blue-600 bg-blue-50'}`}>
                  {chunk.id}
                </span>
                <span className={`text-xs ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>({chunk.length} 字符)</span>
              </div>
              <div className="flex gap-1">
                {editingId !== chunk.id && (
                  <>
                    <button
                      onClick={() => startEdit(chunk)}
                      className={`px-2 py-1 text-xs rounded transition-colors ${isDark ? 'text-gray-400 hover:text-white bg-dark-700 hover:bg-dark-600' : 'text-gray-600 hover:text-gray-900 bg-gray-200 hover:bg-gray-300'}`}
                    >
                      编辑
                    </button>
                    <button
                      onClick={() => deleteChunk(chunk.id)}
                      className="px-2 py-1 text-xs text-red-400 hover:text-red-300 bg-red-400/10 rounded hover:bg-red-400/20 transition-colors"
                    >
                      删除
                    </button>
                  </>
                )}
              </div>
            </div>

            {editingId === chunk.id ? (
              <div className="space-y-2">
                <textarea
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  className={`w-full h-24 rounded-lg p-2 text-sm resize-none focus:outline-none focus:border-blue-500 ${isDark ? 'bg-dark-800 border border-blue-500/50 text-gray-200' : 'bg-white border border-blue-300 text-gray-800'}`}
                  placeholder="输入切片内容..."
                  autoFocus
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => saveEdit(chunk.id)}
                    className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-500 transition-colors"
                  >
                    保存
                  </button>
                  <button
                    onClick={cancelEdit}
                    className={`px-3 py-1 text-xs rounded transition-colors ${isDark ? 'bg-dark-700 text-gray-400 hover:bg-dark-600' : 'bg-gray-200 text-gray-600 hover:bg-gray-300'}`}
                  >
                    取消
                  </button>
                </div>
              </div>
            ) : (
              <p className={`text-sm whitespace-pre-wrap line-clamp-3 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                {chunk.text || <span className={`italic ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>空切片</span>}
              </p>
            )}
          </div>
        ))}
      </div>

      {displayChunks.length === 0 && (
        <div className={`text-center py-8 ${isDark ? 'text-dark-500' : 'text-gray-400'}`}>
          没有切片，点击"新增切片"添加
        </div>
      )}
    </div>
  )
}
