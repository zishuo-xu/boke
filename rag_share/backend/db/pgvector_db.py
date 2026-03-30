"""
PostgreSQL + pgvector 数据库模块

支持向量存储、相似度检索和混合检索
- 第一路召回：向量语义检索（pgvector HNSW 索引）
- 第二路召回：全文关键词检索（PostgreSQL 全文检索）
- 结果融合：RRF 算法
"""

import os
import json
import re
from typing import List, Optional, Tuple
from contextlib import contextmanager

import psycopg2


# PostgreSQL 配置
PG_CONFIG = {
    "host": os.getenv("PG_HOST", "47.107.187.18"),
    "port": int(os.getenv("PG_PORT", "5432")),
    "database": os.getenv("PG_DATABASE", "rag"),
    "user": os.getenv("PG_USER", "rag_user"),
    "password": os.getenv("PG_PASSWORD", "bf9d9e1378856c6ec073dba065fc0d75"),
}


def chinese_tokenize(text: str) -> str:
    """
    中文分词：2-gram 切分，用空格分隔
    用于全文检索的文本预处理
    """
    import re
    # 移除非文字内容
    text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)
    if not text:
        return text

    # 中文 2-gram 切分，用空格分隔
    tokens = []
    i = 0
    while i < len(text):
        if '\u4e00' <= text[i] <= '\u9fff':
            if i + 1 < len(text) and '\u4e00' <= text[i + 1] <= '\u9fff':
                tokens.append(text[i:i + 2])
                i += 2
            else:
                tokens.append(text[i])
                i += 1
        else:
            tokens.append(text[i])
            i += 1

    return ' '.join(tokens)


class PGVectorDB:
    """PostgreSQL pgvector + 全文检索操作类"""

    def __init__(self):
        self._conn = None
        self._ensure_extensions()
        self._ensure_table()

    def _get_conn(self):
        """获取数据库连接"""
        try:
            if self._conn is None or self._conn.closed:
                self._conn = psycopg2.connect(**PG_CONFIG)
        except psycopg2.OperationalError as e:
            print(f"PostgreSQL 连接失败: {e}")
            raise
        return self._conn

    @contextmanager
    def get_cursor(self):
        """获取游标的上下文管理器"""
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

    def _ensure_extensions(self):
        """确保扩展已安装"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        except Exception as e:
            print(f"pgvector 扩展创建失败: {e}")
            raise

    def _ensure_table(self):
        """创建向量存储表"""
        with self.get_cursor() as cursor:
            # document_chunks 表：存储文档片段
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id VARCHAR(100) PRIMARY KEY,
                    text TEXT NOT NULL,
                    length INTEGER NOT NULL,
                    textsearch TSVECTOR,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # chunk_vectors 表：存储向量
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunk_vectors (
                    chunk_id VARCHAR(100) PRIMARY KEY,
                    embedding VECTOR(1024),
                    FOREIGN KEY (chunk_id) REFERENCES document_chunks(id) ON DELETE CASCADE
                );
            """)

            # 创建 GIN 索引（全文检索）
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_document_chunks_textsearch
                ON document_chunks USING GIN (textsearch);
            """)

            # 注意：pgvector 的 HNSW/IVFFlat 索引限制 2000 维
            # 2048 维超限，不创建向量索引，使用顺序扫描（演示够用）

    def insert_chunk(self, chunk_id: str, text: str, length: int, embedding: List[float], metadata: dict = None):
        """插入 chunk 和对应的向量"""
        with self.get_cursor() as cursor:
            # 存储原文和向量，全文检索让 PostgreSQL 自己处理
            cursor.execute("""
                INSERT INTO document_chunks (id, text, length, textsearch, metadata)
                VALUES (%s, %s, %s, to_tsvector('simple', %s), %s)
                ON CONFLICT (id) DO UPDATE SET
                    text = EXCLUDED.text,
                    length = EXCLUDED.length,
                    textsearch = to_tsvector('simple', EXCLUDED.text)
            """, (chunk_id, text, length, text, json.dumps(metadata or {})))

            # 插入向量（截断到 1024 维以兼容 pgvector）
            truncated = embedding[:1024]
            vec_str = "[" + ",".join(str(x) for x in truncated) + "]"
            cursor.execute("""
                INSERT INTO chunk_vectors (chunk_id, embedding)
                VALUES (%s, %s::vector)
                ON CONFLICT (chunk_id) DO UPDATE SET embedding = EXCLUDED.embedding::vector
            """, (chunk_id, vec_str))

    def vector_search(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        """
        第一路召回：向量语义检索

        使用 pgvector 的 HNSW 索引进行近似最近邻搜索
        """
        # 截断查询向量到 1024 维
        query_truncated = query_embedding[:1024]
        vec_str = "[" + ",".join(str(x) for x in query_truncated) + "]"

        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT c.id, 1 - (v.embedding <=> %s::vector) AS similarity
                FROM chunk_vectors v
                JOIN document_chunks c ON v.chunk_id = c.id
                ORDER BY v.embedding <=> %s::vector
                LIMIT %s
            """, (vec_str, vec_str, top_k))

            return [(row[0], float(row[1])) for row in cursor.fetchall()]

    def fulltext_search(self, query_text: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        第二路召回：全文关键词检索

        使用 PostgreSQL ILIKE 进行关键词匹配
        """
        if not query_text:
            return []

        import re

        # 英文单词
        english = re.findall(r'[a-zA-Z0-9_]+', query_text)
        english = [w.lower() for w in english if len(w) >= 2]

        # 中文 bigram（2-gram滑动窗口）
        chinese = re.findall(r'[\u4e00-\u9fff]', query_text)
        chinese_bigrams = []
        for i in range(len(chinese) - 1):
            chinese_bigrams.append(chinese[i] + chinese[i+1])

        # 合并关键词
        keywords = english + chinese_bigrams
        if not keywords:
            return []

        # 限制数量
        keywords = keywords[:5]

        with self.get_cursor() as cursor:
            # 使用 ILIKE 匹配任意关键词
            conditions = ' OR '.join(['text ILIKE %s'] * len(keywords))
            params = [f'%{k}%' for k in keywords]
            cursor.execute(f"""
                SELECT id, text
                FROM document_chunks
                WHERE {conditions}
                LIMIT %s
            """, (*params, top_k))

            results = cursor.fetchall()
            if results:
                # 计算每个 chunk 匹配到的关键词数量
                scores = []
                for row in results:
                    chunk_id, text_content = row
                    # 统计该 chunk 中匹配到的关键词数量
                    match_count = sum(1 for k in keywords if k.lower() in text_content.lower())
                    scores.append((chunk_id, float(match_count) / len(keywords)))
                return scores
            return []

    def hybrid_search(
        self,
        query_embedding: List[float],
        query_text: str,
        top_k: int = 5,
        vector_weight: float = 0.6
    ) -> dict:
        """
        混合检索：向量检索 + 全文检索 + RRF 融合

        参数:
            query_embedding: 查询的向量（用于向量检索）
            query_text: 查询文本（用于全文检索）
            top_k: 返回数量
            vector_weight: 向量检索权重

        返回: {
            "fused_results": [(chunk_id, fused_score), ...],
            "vector_results": [(chunk_id, vector_score), ...],
            "fulltext_results": [(chunk_id, ft_score), ...]
        }
        """
        # 第一路：向量语义检索
        vector_results = self.vector_search(query_embedding, top_k * 3)

        # 第二路：全文关键词检索
        fulltext_results = self.fulltext_search(query_text, top_k * 3)

        if not vector_results and not fulltext_results:
            return {"fused_results": [], "vector_results": [], "fulltext_results": []}

        # 构建分数字典
        vector_scores = {chunk_id: score for chunk_id, score in vector_results}
        fulltext_scores = {chunk_id: score for chunk_id, score in fulltext_results}

        # 获取所有相关 chunk_id
        all_chunk_ids = set(vector_scores.keys()) | set(fulltext_scores.keys())

        # 加权分数融合（直接用相似度分数加权，而非 RRF 排名）
        fused_scores = []
        for chunk_id in all_chunk_ids:
            vec_score = vector_scores.get(chunk_id, 0)
            ft_score = fulltext_scores.get(chunk_id, 0)

            # 标准化：如果某一路没有结果，用0；否则用原始分数
            fused = vector_weight * vec_score + (1 - vector_weight) * ft_score
            fused_scores.append((chunk_id, fused))

        # 按融合分数排序
        fused_scores.sort(key=lambda x: x[1], reverse=True)

        return {
            "fused_results": fused_scores[:top_k],
            "vector_results": vector_results,
            "fulltext_results": fulltext_results
        }

    def get_chunks_by_ids(self, chunk_ids: List[str]) -> List[dict]:
        """根据 ID 列表获取 chunks"""
        if not chunk_ids:
            return []

        placeholders = ','.join(['%s'] * len(chunk_ids))
        with self.get_cursor() as cursor:
            cursor.execute(f"""
                SELECT id, text, length, metadata FROM document_chunks
                WHERE id IN ({placeholders})
            """, chunk_ids)

            return [
                {"id": row[0], "text": row[1], "length": row[2], "metadata": row[3]}
                for row in cursor.fetchall()
            ]

    def clear_all(self):
        """清空所有数据"""
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM chunk_vectors;")
            cursor.execute("DELETE FROM document_chunks;")

    def close(self):
        """关闭连接"""
        if self._conn and not self._conn.closed:
            self._conn.close()
            self._conn = None


# 全局实例（单例）
_db_instance: Optional[PGVectorDB] = None


def get_db() -> Optional[PGVectorDB]:
    """获取数据库实例，如果 PG 不可用则返回 None"""
    global _db_instance

    if _db_instance is not None:
        return _db_instance

    try:
        _db_instance = PGVectorDB()
        return _db_instance
    except Exception as e:
        print(f"PostgreSQL 初始化失败: {e}")
        return None
