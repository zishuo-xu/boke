import random
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class ProcessRequest(BaseModel):
    text: str
    query: str
    chunk_size: int = 100
    overlap: int = 20
    top_k: int = 3
    use_rerank: bool = True
    chunking_strategy: str = "by_chars"  # "by_chars" | "by_sentence" | "by_paragraph"


class Chunk(BaseModel):
    id: str
    text: str
    length: int


class RetrievalResult(BaseModel):
    chunk_id: str
    similarity: float


class RerankedResult(BaseModel):
    chunk_id: str
    original_rank: int
    new_rank: int
    similarity: float


class ProcessResponse(BaseModel):
    preprocessed_text: str
    chunks: List[Chunk]
    vectors: List[List[float]]
    query_vector: List[float]
    retrieval_results: List[RetrievalResult]
    reranked_results: Optional[List[RerankedResult]] = None
    prompt: str
    answer: str


def simple_preprocess(text: str) -> str:
    """Simulate text preprocessing"""
    import re

    # 1. 替换多个空格为单个空格
    text = re.sub(r' +', ' ', text)

    # 2. 处理特殊空白字符（制表符、不间断空格等）
    text = text.replace('\t', ' ')
    text = text.replace('\xa0', ' ')
    text = text.replace('\u3000', ' ')

    # 3. 统一换行符（处理 Windows \r\n 和 Mac \r）
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # 4. 处理无意义符号（多余连字符、特殊引号等）
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    text = text.replace('—', '-').replace('–', '-')

    # 5. 清理行尾多余空格
    lines = [line.rstrip() for line in text.split('\n')]

    # 6. 移除完全空的行，但保留段落分隔
    cleaned_lines = []
    prev_empty = False
    for line in lines:
        is_empty = not line.strip()
        if is_empty:
            if not prev_empty:  # 只保留单个空行作为段落分隔
                cleaned_lines.append('')
            prev_empty = True
        else:
            cleaned_lines.append(line.strip())
            prev_empty = False

    # 7. 移除开头和结尾的空行
    while cleaned_lines and not cleaned_lines[0]:
        cleaned_lines.pop(0)
    while cleaned_lines and not cleaned_lines[-1]:
        cleaned_lines.pop()

    return '\n'.join(cleaned_lines)


def chunk_by_chars(text: str, chunk_size: int, overlap: int) -> List[Chunk]:
    """按字符/词切片"""
    import re
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))

    if has_chinese:
        units = list(text)
    else:
        units = text.split()

    chunks = []
    chunk_id = 0
    start = 0

    while start < len(units):
        end = start + chunk_size
        chunk_units = units[start:end]

        if has_chinese:
            chunk_text = ''.join(chunk_units)
        else:
            chunk_text = ' '.join(chunk_units)

        chunks.append(Chunk(
            id=f"chunk_{chunk_id}",
            text=chunk_text,
            length=len(chunk_units)
        ))

        start += chunk_size - overlap
        chunk_id += 1

        if chunk_size - overlap <= 0:
            break

    return chunks


def chunk_by_sentence(text: str, chunk_size: int, overlap: int) -> List[Chunk]:
    """按句子切片 - 句子不被截断"""
    import re
    # 匹配中英文句子分隔符
    sentences = re.split(r'([。.！？!?\n]+)', text)
    # 合并句子和分隔符
    merged = []
    for i in range(0, len(sentences) - 1, 2):
        merged.append(sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else ''))

    chunks = []
    chunk_id = 0
    current_chunk = []
    current_length = 0

    for sentence in merged:
        sentence_len = len(sentence)
        if current_length + sentence_len <= chunk_size:
            current_chunk.append(sentence)
            current_length += sentence_len
        else:
            # 保存当前 chunk
            if current_chunk:
                chunks.append(Chunk(
                    id=f"chunk_{chunk_id}",
                    text=''.join(current_chunk),
                    length=current_length
                ))
                chunk_id += 1

            # 开始新 chunk，保留 overlap
            if overlap > 0 and current_chunk:
                overlap_text = ''.join(current_chunk)[-overlap:]
                current_chunk = [overlap_text]
                current_length = len(overlap_text)
            else:
                current_chunk = []
                current_length = 0

            # 如果单个句子超过 chunk_size，完整保留不截断
            if sentence_len > chunk_size:
                chunks.append(Chunk(
                    id=f"chunk_{chunk_id}",
                    text=sentence,
                    length=sentence_len
                ))
                chunk_id += 1
            else:
                current_chunk.append(sentence)
                current_length += sentence_len

    # 保存最后一个 chunk
    if current_chunk:
        chunks.append(Chunk(
            id=f"chunk_{chunk_id}",
            text=''.join(current_chunk),
            length=current_length
        ))

    return chunks


def chunk_by_paragraph(text: str, chunk_size: int, overlap: int) -> List[Chunk]:
    """按段落切片 - 段落不被截断"""
    import re
    # 按换行符分割段落
    paragraphs = re.split(r'\n\s*\n', text)

    chunks = []
    chunk_id = 0
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        para_len = len(para)
        para = para.strip()

        if not para:
            continue

        if current_length + para_len <= chunk_size:
            current_chunk.append(para)
            current_length += para_len
        else:
            # 保存当前 chunk
            if current_chunk:
                chunks.append(Chunk(
                    id=f"chunk_{chunk_id}",
                    text='\n\n'.join(current_chunk),
                    length=current_length
                ))
                chunk_id += 1

            # 开始新 chunk，保留 overlap
            if overlap > 0 and current_chunk:
                overlap_text = current_chunk[-1][-overlap:]
                current_chunk = [overlap_text]
                current_length = len(overlap_text)
            else:
                current_chunk = []
                current_length = 0

            # 如果单个段落超过 chunk_size，完整保留不截断
            if para_len > chunk_size:
                chunks.append(Chunk(
                    id=f"chunk_{chunk_id}",
                    text=para,
                    length=para_len
                ))
                chunk_id += 1
            else:
                current_chunk.append(para)
                current_length = para_len

    # 保存最后一个 chunk
    if current_chunk:
        chunks.append(Chunk(
            id=f"chunk_{chunk_id}",
            text='\n\n'.join(current_chunk),
            length=current_length
        ))

    return chunks


def simple_chunk(text: str, chunk_size: int, overlap: int, strategy: str = "by_chars") -> List[Chunk]:
    """根据策略切片"""
    if strategy == "by_sentence":
        return chunk_by_sentence(text, chunk_size, overlap)
    elif strategy == "by_paragraph":
        return chunk_by_paragraph(text, chunk_size, overlap)
    else:
        return chunk_by_chars(text, chunk_size, overlap)


def generate_vector(text: str, dim: int = 10) -> List[float]:
    """调用外部 embedding API 获取文本向量"""
    import os
    import httpx

    api_key = os.getenv("EMBEDDING_API_KEY")
    model = os.getenv("EMBEDDING_MODEL", "doubao-embedding-vision-251215")
    base_url = os.getenv("EMBEDDING_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")

    if not api_key:
        # Fallback to mock if no API key
        import random
        random.seed(hash(text) % 1000)
        return [round(random.uniform(-1, 1), 3) for _ in range(dim)]

    url = f"{base_url}/embeddings/multimodal"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 尝试使用字符串数组格式
    payload = {
        "model": model,
        "input": [
            {
                "type": "text",
                "text": text,
            }
        ],
    }

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        response.raise_for_status()
        data = response.json()

        # 响应格式: {"created":..., "data": {"embedding": [...]}}
        if "data" in data and "embedding" in data["data"]:
            embedding = data["data"]["embedding"]
            return embedding
        else:
            raise ValueError(f"Invalid response: {data}")
    except Exception as e:
        print(f"Embedding API error: {e}, falling back to mock")
        import random
        random.seed(hash(text) % 1000)
        return [round(random.uniform(-1, 1), 3) for _ in range(dim)]


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = sum(a * a for a in v1) ** 0.5
    norm2 = sum(b * b for b in v2) ** 0.5
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return round(dot / (norm1 * norm2), 3)


def rerank_results(retrieval_results: List[RetrievalResult]) -> List[RerankedResult]:
    """Simulate reranking - slightly reorder based on random factor"""
    reranked = []
    for i, rr in enumerate(retrieval_results):
        # Simulate reranking by adding small random changes
        new_rank = i
        if random.random() > 0.7:
            # 30% chance to swap with nearby item
            swap_range = min(2, len(retrieval_results) - 1 - i)
            if swap_range > 0:
                swap_idx = i + random.randint(1, swap_range)
                new_rank = swap_idx

        reranked.append(RerankedResult(
            chunk_id=rr.chunk_id,
            original_rank=i + 1,
            new_rank=new_rank + 1,
            similarity=rr.similarity
        ))

    # Sort by new_rank
    reranked.sort(key=lambda x: x.new_rank)
    return reranked


def build_prompt(query: str, chunks: List[Chunk], top_k: int) -> str:
    """Build the final prompt"""
    system_prompt = "你是一个有用的AI助手。请根据提供的上下文信息回答用户的问题。"

    context_parts = []
    for i, chunk in enumerate(chunks[:top_k]):
        context_parts.append(f"[文档{i+1}]\n{chunk.text}")

    context = "\n\n".join(context_parts)

    prompt = f"""{system_prompt}

上下文信息:
{context}

用户问题: {query}

请根据上下文信息回答问题。"""

    return prompt


@router.post("/rag/process", response_model=ProcessResponse)
async def process_rag(request: ProcessRequest):
    """Process RAG request with mock data"""

    # Step 1: Preprocess
    preprocessed_text = simple_preprocess(request.text)

    # Step 2: Chunk
    chunks = simple_chunk(preprocessed_text, request.chunk_size, request.overlap, request.chunking_strategy)

    # Step 3: Vectorize chunks
    vectors = [generate_vector(chunk.text) for chunk in chunks]

    # Step 4: Vectorize query
    query_vector = generate_vector(request.query)

    # Step 5: Retrieval (similarity calculation)
    similarities = []
    for i, vec in enumerate(vectors):
        sim = cosine_similarity(query_vector, vec)
        similarities.append((i, sim))

    # Sort by similarity descending
    similarities.sort(key=lambda x: x[1], reverse=True)

    # Take top_k
    top_results = similarities[:request.top_k]
    retrieval_results = [
        RetrievalResult(chunk_id=chunks[i].id, similarity=sim)
        for i, sim in top_results
    ]

    # Step 6: Rerank (if enabled)
    reranked_results = None
    top_chunks = [chunks[i] for i, _ in top_results]

    if request.use_rerank:
        reranked_results = rerank_results(retrieval_results)
        # Reorder chunks based on reranking
        reranked_chunk_ids = [r.chunk_id for r in reranked_results]
        top_chunks = [next(c for c in chunks if c.id == bid) for bid in reranked_chunk_ids]

    # Step 7: Build prompt
    prompt = build_prompt(request.query, top_chunks, request.top_k)

    # Step 8: Generate answer (mock)
    answer = f"""根据检索到的上下文信息，我来分析您的问题。

在{len(top_chunks)}个相关文档片段中，最相关的内容提到了相关要点。

示例回答：这个问题涉及到文档中的关键概念。具体来说，RAG流程通过预处理、切片、向量化、检索等步骤，将用户的查询与知识库进行匹配，最终生成准确的回答。

本次检索命中的文档片段：
{chr(10).join([f"- {c.id}: {c.text[:50]}..." for c in top_chunks])}

请注意，这是一个演示用的模拟回答。"""

    return ProcessResponse(
        preprocessed_text=preprocessed_text,
        chunks=chunks,
        vectors=vectors,
        query_vector=query_vector,
        retrieval_results=retrieval_results,
        reranked_results=reranked_results,
        prompt=prompt,
        answer=answer
    )


@router.get("/rag/steps")
async def get_steps():
    """Get the list of RAG steps"""
    return {
        "steps": [
            {"id": 1, "name": "原始文本", "description": "展示输入的原始文档"},
            {"id": 2, "name": "预处理", "description": "文本清洗和标准化"},
            {"id": 3, "name": "切片", "description": "将文本切分成 chunks"},
            {"id": 4, "name": "向量化", "description": "将 chunks 转为向量"},
            {"id": 5, "name": "用户提问", "description": "展示 Query 输入"},
            {"id": 6, "name": "相似度检索", "description": "计算相似度并召回"},
            {"id": 7, "name": "重排", "description": "对召回结果重排序"},
            {"id": 8, "name": "Prompt 组装", "description": "组装最终 Prompt"},
            {"id": 9, "name": "答案生成", "description": "展示最终回答"}
        ]
    }


class EmbedRequest(BaseModel):
    texts: List[str]


class EmbedResponse(BaseModel):
    embeddings: List[List[float]]


@router.post("/rag/embed", response_model=EmbedResponse)
async def get_embeddings(request: EmbedRequest):
    """Get embeddings for arbitrary texts"""
    embeddings = [generate_vector(text) for text in request.texts]
    return {"embeddings": embeddings}
