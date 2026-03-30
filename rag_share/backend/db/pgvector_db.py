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
    中文分词：简单移除非文字内容
    用于全文检索的文本预处理
    """
    import re
    # 移除非文字内容，只保留中文、英文、数字
    text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)
    return text


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

            # 创建 IVFFlat 索引（向量检索）- pgvector支持更高维度
            # 注意：2048维超HNSW的2000维限制，使用IVFFlat
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunk_vectors_ivfflat
                ON chunk_vectors USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """)

    def insert_chunk(self, chunk_id: str, text: str, length: int, embedding: List[float], metadata: dict = None):
        """插入 chunk 和对应的向量、全文检索向量"""
        with self.get_cursor() as cursor:
            # 生成分词后的查询向量
            tokenized_text = chinese_tokenize(text)

            cursor.execute("""
                INSERT INTO document_chunks (id, text, length, textsearch, metadata)
                VALUES (%s, %s, %s, plainto_tsquery('simple', %s), %s)
                ON CONFLICT (id) DO UPDATE SET
                    text = EXCLUDED.text,
                    length = EXCLUDED.length,
                    textsearch = plainto_tsquery('simple', EXCLUDED.text)
            """, (chunk_id, text, length, tokenized_text, json.dumps(metadata or {})))

            # 插入向量
            vec_str = "[" + ",".join(str(x) for x in embedding) + "]"
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
        vec_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

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

        使用 PostgreSQL ILIKE 进行简单的关键词匹配
        """
        # 提取关键词（简单的中文字符串）
        keywords = chinese_tokenize(query_text)
        if not keywords or len(keywords) < 2:
            return []

        # 取前4个字符作为关键词
        keywords = keywords[:4]

        with self.get_cursor() as cursor:
            # 使用 ILIKE 进行模糊匹配
            cursor.execute("""
                SELECT id, LENGTH(text) as match_len
                FROM document_chunks
                WHERE text ILIKE %s
                ORDER BY match_len ASC
                LIMIT %s
            """, (f'%{keywords}%', top_k))

            results = cursor.fetchall()
            if results:
                # 归一化分数
                max_len = max(float(row[1]) for row in results) if results else 1
                return [(row[0], 1.0 - float(row[1]) / max_len) for row in results]
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

        # 构建排名字典（用于 RRF）
        def rrf_rank(results: List[Tuple[str, float]], k: int = 60) -> dict:
            """RRF 排名：1 / (k + rank)"""
            ranks = {}
            for rank, (chunk_id, _) in enumerate(results):
                ranks[chunk_id] = 1.0 / (k + rank + 1)
            return ranks

        vector_ranks = rrf_rank(vector_results)
        fulltext_ranks = rrf_rank(fulltext_results)

        # 获取所有相关 chunk_id
        all_chunk_ids = set(vector_ranks.keys()) | set(fulltext_ranks.keys())

        # RRF 融合
        fused_scores = []
        for chunk_id in all_chunk_ids:
            vec_rank_score = vector_ranks.get(chunk_id, 0)
            ft_rank_score = fulltext_ranks.get(chunk_id, 0)

            # 按权重融合排名分数
            fused = vector_weight * vec_rank_score + (1 - vector_weight) * ft_rank_score
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
