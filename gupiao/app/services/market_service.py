from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy.orm import Session

from app.config import settings
from app.models.stock import Stock
from app.utils.data_fetcher import DataFetcher
from app.services.cache_service import cache_service


class MarketService:
    """市场数据服务"""

    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.stock_cache_ttl = settings.STOCK_CACHE_TTL
        self.fund_cache_ttl = settings.FUND_CACHE_TTL
        self.history_cache_ttl = settings.HISTORY_CACHE_TTL

    def get_stock_realtime(
        self,
        db: Session,
        user_id: int,
        stock_id: int,
        force_refresh: bool = False
    ) -> Optional[Dict]:
        """
        获取股票实时数据

        Args:
            db: 数据库会话
            user_id: 用户ID
            stock_id: 股票ID
            force_refresh: 是否强制刷新

        Returns:
            股票数据字典
        """
        # 获取股票信息
        stock = db.query(Stock).filter(
            Stock.id == stock_id,
            Stock.user_id == user_id
        ).first()

        if not stock:
            return None

        # 检查是否为股票类型
        if stock.type != 'stock':
            return None

        cache_key = f"stock:realtime:{stock.code}"

        # 如果不强制刷新，先尝试从缓存获取
        if not force_refresh:
            cached_data = cache_service.get(cache_key)
            if cached_data:
                return cached_data

        # 从AKShare获取数据
        data = self.data_fetcher.get_stock_realtime_data(stock.code)

        if data:
            # 更新缓存
            cache_service.set(cache_key, data, self.stock_cache_ttl)

        return data

    def get_stock_by_code(
        self,
        stock_code: str,
        force_refresh: bool = False
    ) -> Optional[Dict]:
        """
        根据股票代码获取实时数据（无需登录）

        Args:
            stock_code: 股票代码
            force_refresh: 是否强制刷新

        Returns:
            股票数据字典
        """
        cache_key = f"stock:code:{stock_code}"

        # 如果不强制刷新，先尝试从缓存获取
        if not force_refresh:
            cached_data = cache_service.get(cache_key)
            if cached_data:
                return cached_data

        # 从AKShare获取数据
        data = self.data_fetcher.get_stock_realtime_data(stock_code)

        if data:
            # 更新缓存
            cache_service.set(cache_key, data, self.stock_cache_ttl)

        return data

    def get_fund_realtime(
        self,
        db: Session,
        user_id: int,
        stock_id: int,
        force_refresh: bool = False
    ) -> Optional[Dict]:
        """
        获取基金实时数据

        Args:
            db: 数据库会话
            user_id: 用户ID
            stock_id: 基金ID
            force_refresh: 是否强制刷新

        Returns:
            基金数据字典
        """
        # 获取基金信息
        stock = db.query(Stock).filter(
            Stock.id == stock_id,
            Stock.user_id == user_id
        ).first()

        if not stock:
            return None

        # 检查是否为基金类型
        if stock.type != 'fund':
            return None

        cache_key = f"fund:realtime:{stock.code}"

        # 如果不强制刷新，先尝试从缓存获取
        if not force_refresh:
            cached_data = cache_service.get(cache_key)
            if cached_data:
                return cached_data

        # 从AKShare获取数据
        data = self.data_fetcher.get_fund_realtime_data(stock.code)

        if data:
            # 更新缓存
            cache_service.set(cache_key, data, self.fund_cache_ttl)

        return data

    def get_stock_history(
        self,
        db: Session,
        user_id: int,
        stock_id: int,
        period: str = "30d",
        force_refresh: bool = False
    ) -> List[Dict]:
        """
        获取股票历史数据

        Args:
            db: 数据库会话
            user_id: 用户ID
            stock_id: 股票ID
            period: 时间周期
            force_refresh: 是否强制刷新

        Returns:
            历史数据列表
        """
        # 获取股票信息
        stock = db.query(Stock).filter(
            Stock.id == stock_id,
            Stock.user_id == user_id
        ).first()

        if not stock or stock.type != 'stock':
            return []

        cache_key = f"stock:history:{stock.code}:{period}"

        # 如果不强制刷新，先尝试从缓存获取
        if not force_refresh:
            cached_data = cache_service.get(cache_key)
            if cached_data:
                return cached_data

        # 从AKShare获取数据
        data = self.data_fetcher.get_stock_history_data(stock.code, period)

        if data:
            # 更新缓存
            cache_service.set(cache_key, data, self.history_cache_ttl)

        return data

    def get_fund_history(
        self,
        db: Session,
        user_id: int,
        stock_id: int,
        period: str = "30d",
        force_refresh: bool = False
    ) -> List[Dict]:
        """
        获取基金历史数据

        Args:
            db: 数据库会话
            user_id: 用户ID
            stock_id: 基金ID
            period: 时间周期
            force_refresh: 是否强制刷新

        Returns:
            历史数据列表
        """
        # 获取基金信息
        stock = db.query(Stock).filter(
            Stock.id == stock_id,
            Stock.user_id == user_id
        ).first()

        if not stock or stock.type != 'fund':
            return []

        cache_key = f"fund:history:{stock.code}:{period}"

        # 如果不强制刷新，先尝试从缓存获取
        if not force_refresh:
            cached_data = cache_service.get(cache_key)
            if cached_data:
                return cached_data

        # 从AKShare获取数据
        data = self.data_fetcher.get_fund_history_data(stock.code, period)

        if data:
            # 更新缓存
            cache_service.set(cache_key, data, self.history_cache_ttl)

        return data

    def get_batch_stocks_realtime(
        self,
        db: Session,
        user_id: int,
        stock_ids: List[int],
        force_refresh: bool = False
    ) -> Dict[str, Dict]:
        """
        批量获取股票实时数据

        Args:
            db: 数据库会话
            user_id: 用户ID
            stock_ids: 股票ID列表
            force_refresh: 是否强制刷新

        Returns:
            字典：{code: stock_data}
        """
        # 获取股票列表
        stocks = db.query(Stock).filter(
            Stock.id.in_(stock_ids),
            Stock.user_id == user_id,
            Stock.type == 'stock'
        ).all()

        results = {}
        for stock in stocks:
            data = self.get_stock_realtime(db, user_id, stock.id, force_refresh)
            if data:
                results[stock.code] = data

        return results

    def refresh_all_stocks(self, db: Session, user_id: int) -> int:
        """
        刷新用户所有股票数据

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            成功刷新的数量
        """
        # 获取所有股票
        stocks = db.query(Stock).filter(
            Stock.user_id == user_id,
            Stock.type == 'stock'
        ).all()

        count = 0
        for stock in stocks:
            data = self.get_stock_realtime(db, user_id, stock.id, force_refresh=True)
            if data:
                count += 1

        return count

    def refresh_all_funds(self, db: Session, user_id: int) -> int:
        """
        刷新用户所有基金数据

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            成功刷新的数量
        """
        # 获取所有基金
        funds = db.query(Stock).filter(
            Stock.user_id == user_id,
            Stock.type == 'fund'
        ).all()

        count = 0
        for fund in funds:
            data = self.get_fund_realtime(db, user_id, fund.id, force_refresh=True)
            if data:
                count += 1

        return count


# 全局市场服务实例
market_service = MarketService()
