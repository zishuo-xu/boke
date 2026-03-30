import random
import math
import re
import os
import httpx
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from db.pgvector_db import PG_CONFIG

router = APIRouter()


class ProcessRequest(BaseModel):
    text: str
    query: str
    chunk_size: int = 100
    overlap: int = 20
    top_k: int = 3
    use_rerank: bool = True
    chunking_strategy: str = "by_chars"  # "by_chars" | "by_sentence" | "by_paragraph"
    use_pg: bool = False  # 是否使用 PostgreSQL 存储和检索
    use_hybrid_search: bool = False  # 是否使用混合检索（仅 use_pg=True 时有效）


class Chunk(BaseModel):
    id: str
    text: str
    length: int


class RetrievalResult(BaseModel):
    chunk_id: str
    similarity: float
    vector_score: Optional[float] = None
    fulltext_score: Optional[float] = None


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
    storage_mode: str = "in_memory"  # "in_memory" | "postgresql"
    search_mode: str = "vector"  # "vector" | "hybrid"


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


def generate_answer(prompt: str) -> str:
    """调用外部 LLM API 生成答案"""
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL", "MiniMax-M2.7")
    base_url = os.getenv("LLM_BASE_URL", "https://newapi.hizui.cn/v1")

    if not api_key:
        return "LLM API key not configured"

    url = f"{base_url}/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=60.0)
        response.raise_for_status()
        data = response.json()
        # MiniMax 推理模型返回 reasoning_content，普通模型返回 content
        message = data["choices"][0]["message"]
        content = message.get("content", "") or message.get("reasoning_content", "")
        if not content:
            content = message.get("reasoning_details", [{}])[0].get("text", "") if message.get("reasoning_details") else ""
        return content
    except Exception as e:
        print(f"LLM API error: {e}")
        return f"LLM API error: {str(e)}"


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = sum(a * a for a in v1) ** 0.5
    norm2 = sum(b * b for b in v2) ** 0.5
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return round(dot / (norm1 * norm2), 3)


def rerank_results(retrieval_results: List[RetrievalResult], chunks: List[Chunk], query: str) -> List[RerankedResult]:
    """
    使用 BM25 + 向量相似度融合实现真实重排

    原理：
    1. BM25：基于关键词的传统信息检索算法，衡量 query 中的词在文档中的重要程度
    2. 向量相似度：之前计算的语义相似度
    3. 融合：将 BM25 分数和向量相似度加权组合，得到最终相关性分数
    """
    # 简单中文分词（基于字符匹配）
    def tokenize(text: str) -> List[str]:
        """简单分词：去除标点，按字符 n-gram 切分"""
        text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)  # 只保留中文和字母数字
        if len(text) == 0:
            return []
        # 2-gram 切分
        tokens = []
        for i in range(len(text) - 1):
            tokens.append(text[i:i+2])
        return tokens

    # 计算 BM25 分数
    def bm25_score(doc_tokens: List[str], query_tokens: List[str], avg_doc_len: float, doc_len: int) -> float:
        """计算单个文档的 BM25 分数"""
        k1 = 1.5  # 词频饱和参数
        b = 0.75  # 文档长度归一化参数

        score = 0.0
        doc_tf = {}
        for token in doc_tokens:
            doc_tf[token] = doc_tf.get(token, 0) + 1

        for token in query_tokens:
            if token not in doc_tf:
                continue
            tf = doc_tf[token]
            # IDF 设为固定值（简化版）
            idf = math.log((len(chunks) + 0.5) / 0.5 + 1)
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_len / avg_doc_len))
            score += idf * (numerator / denominator)

        return score

    query_tokens = tokenize(query)
    if not query_tokens:
        # 无法分词时，返回原排序
        return [
            RerankedResult(
                chunk_id=rr.chunk_id,
                original_rank=i + 1,
                new_rank=i + 1,
                similarity=rr.similarity
            )
            for i, rr in enumerate(retrieval_results)
        ]

    # 获取需要重排的 chunks
    chunk_map = {c.id: c for c in chunks}
    target_chunks = [chunk_map[rr.chunk_id] for rr in retrieval_results]

    # 计算每个 chunk 的 BM25 分数
    doc_tokens_list = [tokenize(c.text) for c in target_chunks]
    avg_doc_len = sum(len(t) for t in doc_tokens_list) / max(len(doc_tokens_list), 1)

    bm25_scores = []
    for i, (chunk, tokens) in enumerate(zip(target_chunks, doc_tokens_list)):
        score = bm25_score(tokens, query_tokens, avg_doc_len, len(tokens))
        bm25_scores.append(score)

    # 归一化 BM25 分数到 [0, 1]
    max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1
    min_bm25 = min(bm25_scores) if bm25_scores else 0
    bm25_range = max_bm25 - min_bm25 if max_bm25 - min_bm25 > 0 else 1

    # 归一化向量相似度
    max_sim = max(rr.similarity for rr in retrieval_results) if retrieval_results else 1
    max_sim = max_sim if max_sim > 0 else 1

    # 融合分数：BM25权重0.4，向量相似度权重0.6
    bm25_weight = 0.4
    vec_weight = 0.6

    fused_scores = []
    for i, rr in enumerate(retrieval_results):
        norm_bm25 = (bm25_scores[i] - min_bm25) / bm25_range
        norm_vec = rr.similarity / max_sim
        fused = bm25_weight * norm_bm25 + vec_weight * norm_vec
        fused_scores.append(fused)

    # 根据融合分数重新排序
    indexed = list(enumerate(fused_scores))
    indexed.sort(key=lambda x: x[1], reverse=True)

    # 构建重排结果
    reranked = []
    for new_rank, (orig_idx, _) in enumerate(indexed):
        rr = retrieval_results[orig_idx]
        reranked.append(RerankedResult(
            chunk_id=rr.chunk_id,
            original_rank=orig_idx + 1,
            new_rank=new_rank + 1,
            similarity=rr.similarity
        ))

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
    """Process RAG request with in-memory or PostgreSQL mode"""

    # Step 1: Preprocess
    preprocessed_text = simple_preprocess(request.text)

    # Step 2: Chunk
    chunks = simple_chunk(preprocessed_text, request.chunk_size, request.overlap, request.chunking_strategy)

    # Step 3: Vectorize chunks
    vectors = [generate_vector(chunk.text) for chunk in chunks]

    # Step 4: Vectorize query
    query_vector = generate_vector(request.query)

    # Step 5: Retrieval (similarity calculation)
    # 确定存储和检索模式
    storage_mode = "postgresql" if request.use_pg else "in_memory"
    search_mode = "hybrid" if request.use_hybrid_search else "vector"

    retrieval_results = []
    reranked_results = None
    top_chunks = chunks[:request.top_k]

    if request.use_pg:
        # PostgreSQL 模式
        from db import get_db

        db = get_db()
        if db is not None:
            try:
                # 插入 chunks 和 vectors 到 PG
                for chunk, vec in zip(chunks, vectors):
                    db.insert_chunk(chunk.id, chunk.text, chunk.length, vec)

                # 根据模式选择检索方式
                chunk_map = {c.id: c for c in chunks}

                if request.use_hybrid_search:
                    # 混合检索：向量检索 + 全文检索 + RRF 融合
                    search_data = db.hybrid_search(query_vector, request.query, request.top_k)
                    search_mode = "hybrid"

                    # 构建包含向量分数和全文检索分数的结果
                    vector_dict = {v[0]: v[1] for v in search_data["vector_results"]}
                    ft_dict = {f[0]: f[1] for f in search_data["fulltext_results"]}

                    retrieval_results = []
                    for chunk_id, fused_score in search_data["fused_results"]:
                        if chunk_id in chunk_map:
                            retrieval_results.append(RetrievalResult(
                                chunk_id=chunk_id,
                                similarity=fused_score,
                                vector_score=vector_dict.get(chunk_id),
                                fulltext_score=ft_dict.get(chunk_id)
                            ))

                    top_chunks = [chunk_map[cr.chunk_id] for cr in retrieval_results]
                else:
                    # 纯向量检索
                    search_results = db.vector_search(query_vector, request.top_k)
                    search_mode = "vector"

                    retrieval_results = [
                        RetrievalResult(chunk_id=chunk_id, similarity=sim, vector_score=sim)
                        for chunk_id, sim in search_results
                        if chunk_id in chunk_map
                    ]

                    top_chunks = [chunk_map[cr.chunk_id] for cr in retrieval_results]

            except Exception as e:
                print(f"PostgreSQL 错误: {e}，回退到内存模式")
                storage_mode = "in_memory_fallback"
                # 回退到内存计算
                similarities = []
                for i, vec in enumerate(vectors):
                    sim = cosine_similarity(query_vector, vec)
                    similarities.append((i, sim))
                similarities.sort(key=lambda x: x[1], reverse=True)
                top_results = similarities[:request.top_k]
                retrieval_results = [
                    RetrievalResult(chunk_id=chunks[i].id, similarity=sim)
                    for i, sim in top_results
                ]
                top_chunks = [chunks[i] for i, _ in top_results]
        else:
            print("PostgreSQL 不可用，回退到内存模式")
            storage_mode = "in_memory_fallback"
            # 回退到内存计算
            similarities = []
            for i, vec in enumerate(vectors):
                sim = cosine_similarity(query_vector, vec)
                similarities.append((i, sim))
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_results = similarities[:request.top_k]
            retrieval_results = [
                RetrievalResult(chunk_id=chunks[i].id, similarity=sim)
                for i, sim in top_results
            ]
            top_chunks = [chunks[i] for i, _ in top_results]
    else:
        # 内存模式（原有逻辑）
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
        top_chunks = [chunks[i] for i, _ in top_results]

    # Step 6: Rerank (if enabled)
    if request.use_rerank and retrieval_results:
        reranked_results = rerank_results(retrieval_results, chunks, request.query)
        # Reorder chunks based on reranking
        reranked_chunk_ids = [r.chunk_id for r in reranked_results]
        top_chunks = [next(c for c in chunks if c.id == bid) for bid in reranked_chunk_ids]

    # Step 7: Build prompt
    prompt = build_prompt(request.query, top_chunks, request.top_k)

    # Step 8: Generate answer using LLM
    answer = generate_answer(prompt)

    return ProcessResponse(
        preprocessed_text=preprocessed_text,
        chunks=chunks,
        vectors=vectors,
        query_vector=query_vector,
        retrieval_results=retrieval_results,
        reranked_results=reranked_results,
        prompt=prompt,
        answer=answer,
        storage_mode=storage_mode,
        search_mode=search_mode
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
        ],
        "storage_modes": {
            "in_memory": "内存模式：向量存储在内存中，重启后丢失",
            "postgresql": "PostgreSQL 模式：向量持久化到 pgvector 数据库"
        },
        "search_modes": {
            "vector": "纯向量检索：基于余弦相似度的语义搜索",
            "hybrid": "混合检索：向量检索 + BM25 关键词融合"
        }
    }


@router.get("/rag/pg-status")
async def get_pg_status():
    """Check PostgreSQL connection status"""
    from db import get_db

    db = get_db()
    if db is not None:
        try:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
            return {
                "status": "connected",
                "version": version,
                "host": PG_CONFIG["host"],
                "database": PG_CONFIG["database"]
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    return {"status": "disconnected", "message": "PostgreSQL 不可用或 pgvector 未安装"}


@router.post("/rag/pg-clear")
async def clear_pg_data():
    """Clear all data from PostgreSQL"""
    from db import get_db

    db = get_db()
    if db is not None:
        try:
            db.clear_all()
            return {"status": "success", "message": "PostgreSQL 数据已清空"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    return {"status": "error", "message": "PostgreSQL 不可用"}


class EmbedRequest(BaseModel):
    texts: List[str]


class EmbedResponse(BaseModel):
    embeddings: List[List[float]]


@router.post("/rag/embed", response_model=EmbedResponse)
async def get_embeddings(request: EmbedRequest):
    """Get embeddings for arbitrary texts"""
    embeddings = [generate_vector(text) for text in request.texts]
    return {"embeddings": embeddings}
