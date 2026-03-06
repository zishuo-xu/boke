from typing import Any, Optional, Dict
import time
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """缓存服务（LRU缓存实现）"""

    def __init__(self, max_size: int = 1000):
        """
        初始化缓存服务

        Args:
            max_size: 最大缓存条目数
        """
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.max_size = max_size

    def get(self, key: str) -> Optional[Any]:
        """
        从缓存获取数据

        Args:
            key: 缓存键

        Returns:
            缓存的数据，不存在或已过期返回None
        """
        if key in self.cache:
            # 移动到末尾（最近使用）
            cache_entry = self.cache.pop(key)
            self.cache[key] = cache_entry

            # 检查是否过期
            if time.time() < cache_entry['expire_time']:
                return cache_entry['data']
            else:
                # 过期，删除
                del self.cache[key]
                logger.debug(f"缓存已过期: {key}")
                return None

        return None

    def set(self, key: str, data: Any, ttl: int = 300):
        """
        设置缓存

        Args:
            key: 缓存键
            data: 缓存数据
            ttl: 过期时间（秒）
        """
        # 如果缓存已满，删除最久未使用的
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            logger.debug(f"缓存已满，删除最旧数据: {oldest_key}")

        # 设置缓存
        self.cache[key] = {
            'data': data,
            'expire_time': time.time() + ttl
        }

    def delete(self, key: str):
        """
        删除缓存

        Args:
            key: 缓存键
        """
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"删除缓存: {key}")

    def clear(self):
        """清空所有缓存"""
        self.cache.clear()
        logger.info("缓存已清空")

    def delete_pattern(self, pattern: str):
        """
        删除匹配模式的缓存

        Args:
            pattern: 模式（支持*通配符）
        """
        keys_to_delete = []

        for key in self.cache.keys():
            if pattern in key:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self.cache[key]

        logger.info(f"删除匹配模式的缓存: {pattern}, 共{len(keys_to_delete)}条")

    def get_size(self) -> int:
        """
        获取当前缓存大小

        Returns:
            缓存条目数
        """
        return len(self.cache)


# 全局缓存实例
cache_service = CacheService(max_size=1000)
