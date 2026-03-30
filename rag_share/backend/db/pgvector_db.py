"""
PostgreSQL + pgvector 数据库模块

支持向量存储、相似度检索和混合检索
"""

import os
import json
import hashlib
from typing import List, Optional, Tuple
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import execute_values


# PostgreSQL 配置
PG_CONFIG = {
    "host": os.getenv("PG_HOST", "47.107.187.18"),
    "port": int(os.getenv("PG_PORT", "5432")),
    "database": os.getenv("PG_DATABASE", "postgres"),
    "user": os.getenv("PG_USER", "root"),
    "password": os.getenv("PG_PASSWORD", "Y/_c3t#&#n5a4!G"),
}


class PGVectorDB:
    """PostgreSQL pgvector 操作类"""

    def __init__(self):
        self._conn = None
        self._ensure_vector_extension()
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

    def _ensure_vector_extension(self):
        """确保 pgvector 扩展已安装"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        except Exception as e:
            print(f"pgvector 扩展创建失败: {e}")
            raise

    def _ensure_table(self):
        """创建向量存储表"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id VARCHAR(100) PRIMARY KEY,
                    text TEXT NOT NULL,
                    length INTEGER NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunk_vectors (
                    chunk_id VARCHAR(100) PRIMARY KEY,
                    embedding VECTOR(1024),
                    FOREIGN KEY (chunk_id) REFERENCES document_chunks(id) ON DELETE CASCADE
                );
            """)
            # 创建 HNSW 索引（如果不存在）
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunk_vectors_hnsw
                ON chunk_vectors USING hnsw (embedding vector_cosine_ops);
            """)

    def insert_chunk(self, chunk_id: str, text: str, length: int, embedding: List[float], metadata: dict = None):
        """插入 chunk 和对应的向量"""
        with self.get_cursor() as cursor:
            # 插入文档
            cursor.execute("""
                INSERT INTO document_chunks (id, text, length, metadata)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET text = EXCLUDED.text, length = EXCLUDED.length
            """, (chunk_id, text, length, json.dumps(metadata or {})))

            # 插入向量（转换为 PostgreSQL VECTOR 格式）
            vec_str = "[" + ",".join(str(x) for x in embedding) + "]"
            cursor.execute("""
                INSERT INTO chunk_vectors (chunk_id, embedding)
                VALUES (%s, %s::vector)
                ON CONFLICT (chunk_id) DO UPDATE SET embedding = EXCLUDED.embedding::vector
            """, (chunk_id, vec_str))

    def vector_search(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        """
        纯向量检索：使用余弦相似度搜索最相似的 chunks

        返回: [(chunk_id, similarity_score), ...]
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

    def hybrid_search(
        self,
        query_embedding: List[float],
        query_text: str,
        top_k: int = 5,
        vector_weight: float = 0.6
    ) -> List[Tuple[str, float]]:
        """
        混合检索：结合向量相似度和 BM25 关键词匹配

        参数:
            query_embedding: 查询的向量
            query_text: 查询文本（用于 BM25）
            top_k: 返回数量
            vector_weight: 向量检索权重 (0-1)，BM25 权重为 1-vector_weight

        返回: [(chunk_id, fused_score), ...]
        """
        vec_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        with self.get_cursor() as cursor:
            # 向量检索结果
            cursor.execute("""
                SELECT v.chunk_id, 1 - (v.embedding <=> %s::vector) AS vec_sim
                FROM chunk_vectors v
                ORDER BY v.embedding <=> %s::vector
                LIMIT %s
            """, (vec_str, vec_str, top_k * 3))  # 多取一些用于融合

            vector_results = {row[0]: float(row[1]) for row in cursor.fetchall()}

            if not vector_results:
                return []

            # 获取对应文档用于 BM25 计算
            chunk_ids = list(vector_results.keys())
            placeholders = ','.join(['%s'] * len(chunk_ids))
            cursor.execute(f"""
                SELECT id, text FROM document_chunks WHERE id IN ({placeholders})
            """, chunk_ids)

            docs = {row[0]: row[1] for row in cursor.fetchall()}

            # 简单的 BM25 实现
            def simple_tokenize(text: str) -> List[str]:
                import re
                text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)
                return [text[i:i+2] for i in range(len(text) - 1)]

            query_tokens = simple_tokenize(query_text)
            if not query_tokens:
                # 无法分词时返回纯向量结果
                return [(k, v) for k, v in sorted(vector_results.items(), key=lambda x: x[1], reverse=True)[:top_k]]

            # 计算 BM25 分数
            avg_doc_len = sum(len(d) for d in docs.values()) / max(len(docs), 1)
            k1, b = 1.5, 0.75

            bm25_scores = {}
            for chunk_id, text in docs.items():
                doc_tokens = simple_tokenize(text)
                doc_tf = {}
                for token in doc_tokens:
                    doc_tf[token] = doc_tf.get(token, 0) + 1

                score = 0.0
                for token in query_tokens:
                    if token not in doc_tf:
                        continue
                    tf = doc_tf[token]
                    idf = 1.0  # 简化 IDF
                    score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (len(text) / avg_doc_len)))
                bm25_scores[chunk_id] = score

            # 归一化分数
            max_vec = max(vector_results.values()) if vector_results else 1
            max_bm25 = max(bm25_scores.values()) if bm25_scores else 1

            # RRF 融合
            fused_scores = {}
            for chunk_id in vector_results:
                norm_vec = vector_results[chunk_id] / max_vec if max_vec > 0 else 0
                norm_bm25 = bm25_scores.get(chunk_id, 0) / max_bm25 if max_bm25 > 0 else 0
                fused_scores[chunk_id] = vector_weight * norm_vec + (1 - vector_weight) * norm_bm25

            # 返回 Top-K
            sorted_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
            return sorted_results[:top_k]

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
