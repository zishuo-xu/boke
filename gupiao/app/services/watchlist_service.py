from typing import Optional, List
import re
from sqlalchemy.orm import Session

from app.models.stock import Stock
from app.models.group import Group
from app.schemas.watchlist import StockCreate, StockUpdate, GroupCreate, GroupUpdate


class WatchlistService:
    """自选管理服务"""

    @staticmethod
    def validate_stock_code(code: str, stock_type: str) -> bool:
        """
        验证标的代码格式

        Args:
            code: 标的代码
            stock_type: 标的类型（stock/fund）

        Returns:
            是否有效
        """
        if stock_type == 'stock':
            # A股：6位数字
            if re.match(r'^\d{6}$', code):
                return True
            # 港股：5位数字 + .HK
            if re.match(r'^\d{5}\.HK$', code.upper()):
                return True
            # 美股：字母组合
            if re.match(r'^[A-Z]+$', code.upper()):
                return True
            return False
        elif stock_type == 'fund':
            # 基金：6位数字
            return bool(re.match(r'^\d{6}$', code))

        return False

    @staticmethod
    def detect_market(code: str) -> str:
        """
        判断股票市场

        Args:
            code: 股票代码

        Returns:
            市场类型：A股/港股/美股
        """
        code_upper = code.upper()

        if code.startswith('6') or code.startswith('0') or code.startswith('3'):
            return 'A股'
        elif code_upper.endswith('.HK'):
            return '港股'
        else:
            return '美股'

    @staticmethod
    def add_stock(db: Session, user_id: int, stock_data: StockCreate) -> Stock:
        """
        添加标的

        Args:
            db: 数据库会话
            user_id: 用户ID
            stock_data: 标的数据

        Returns:
            创建的标的对象

        Raises:
            ValueError: 代码格式错误或已存在
        """
        # 验证代码格式
        if not WatchlistService.validate_stock_code(stock_data.code, stock_data.type):
            raise ValueError(f"{stock_data.type}代码格式错误")

        # 检查是否已存在
        existing = db.query(Stock).filter(
            Stock.user_id == user_id,
            Stock.code == stock_data.code,
            Stock.type == stock_data.type
        ).first()

        if existing:
            raise ValueError("该标的已存在")

        # 验证分组是否存在
        if stock_data.group_id:
            group = db.query(Group).filter(
                Group.id == stock_data.group_id,
                Group.user_id == user_id
            ).first()

            if not group:
                raise ValueError("分组不存在")

        # 获取市场信息
        market = None
        if stock_data.type == 'stock':
            market = WatchlistService.detect_market(stock_data.code)

        # 创建标的
        db_stock = Stock(
            user_id=user_id,
            code=stock_data.code.upper(),
            name=stock_data.name,
            type=stock_data.type,
            market=market,
            group_id=stock_data.group_id,
            sort_order=0
        )

        db.add(db_stock)
        db.commit()
        db.refresh(db_stock)

        return db_stock

    @staticmethod
    def get_stocks(db: Session, user_id: int, group_id: Optional[int] = None) -> List[Stock]:
        """
        获取用户的自选列表

        Args:
            db: 数据库会话
            user_id: 用户ID
            group_id: 分组ID（可选）

        Returns:
            标的列表
        """
        query = db.query(Stock).filter(Stock.user_id == user_id)

        if group_id is not None:
            query = query.filter(Stock.group_id == group_id)

        return query.order_by(Stock.sort_order, Stock.created_at).all()

    @staticmethod
    def get_stock_by_id(db: Session, user_id: int, stock_id: int) -> Optional[Stock]:
        """
        根据ID获取标的

        Args:
            db: 数据库会话
            user_id: 用户ID
            stock_id: 标的ID

        Returns:
            标的对象，不存在返回None
        """
        return db.query(Stock).filter(
            Stock.id == stock_id,
            Stock.user_id == user_id
        ).first()

    @staticmethod
    def update_stock(db: Session, user_id: int, stock_id: int, stock_data: StockUpdate) -> Stock:
        """
        更新标的

        Args:
            db: 数据库会话
            user_id: 用户ID
            stock_id: 标的ID
            stock_data: 更新数据

        Returns:
            更新后的标的对象

        Raises:
            ValueError: 标的不存在
        """
        stock = WatchlistService.get_stock_by_id(db, user_id, stock_id)

        if not stock:
            raise ValueError("标的不存在")

        # 验证分组是否存在
        if stock_data.group_id is not None:
            if stock_data.group_id == 0:
                # 移动到未分组
                stock.group_id = None
            else:
                group = db.query(Group).filter(
                    Group.id == stock_data.group_id,
                    Group.user_id == user_id
                ).first()

                if not group:
                    raise ValueError("分组不存在")

                stock.group_id = stock_data.group_id

        # 更新其他字段
        if stock_data.name is not None:
            stock.name = stock_data.name

        if stock_data.sort_order is not None:
            stock.sort_order = stock_data.sort_order

        db.commit()
        db.refresh(stock)

        return stock

    @staticmethod
    def delete_stock(db: Session, user_id: int, stock_id: int) -> bool:
        """
        删除标的

        Args:
            db: 数据库会话
            user_id: 用户ID
            stock_id: 标的ID

        Returns:
            是否删除成功

        Raises:
            ValueError: 标的不存在
        """
        stock = WatchlistService.get_stock_by_id(db, user_id, stock_id)

        if not stock:
            raise ValueError("标的不存在")

        db.delete(stock)
        db.commit()

        return True

    @staticmethod
    def search_stocks(db: Session, user_id: int, keyword: str, stock_type: Optional[str] = None) -> List[Stock]:
        """
        模糊搜索标的

        Args:
            db: 数据库会话
            user_id: 用户ID
            keyword: 搜索关键词
            stock_type: 标的类型筛选

        Returns:
            标的列表
        """
        query = db.query(Stock).filter(Stock.user_id == user_id)

        # 类型筛选
        if stock_type:
            query = query.filter(Stock.type == stock_type)

        # 关键词搜索
        keyword_upper = keyword.upper()
        query = query.filter(
            (Stock.code.like(f'%{keyword_upper}%')) |
            (Stock.name.like(f'%{keyword}%'))
        )

        return query.all()


class GroupService:
    """分组服务"""

    @staticmethod
    def create_group(db: Session, user_id: int, group_data: GroupCreate) -> Group:
        """
        创建分组

        Args:
            db: 数据库会话
            user_id: 用户ID
            group_data: 分组数据

        Returns:
            创建的分组对象
        """
        # 检查分组名称是否重复
        existing = db.query(Group).filter(
            Group.user_id == user_id,
            Group.name == group_data.name
        ).first()

        if existing:
            raise ValueError("分组名称已存在")

        # 创建分组
        db_group = Group(
            user_id=user_id,
            name=group_data.name,
            sort_order=group_data.sort_order or 0
        )

        db.add(db_group)
        db.commit()
        db.refresh(db_group)

        return db_group

    @staticmethod
    def get_groups(db: Session, user_id: int) -> List[Group]:
        """
        获取用户的分组列表

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            分组列表
        """
        groups = db.query(Group).filter(
            Group.user_id == user_id
        ).order_by(Group.sort_order, Group.created_at).all()

        # 为每个分组添加标的数量
        for group in groups:
            group.stock_count = db.query(Stock).filter(
                Stock.group_id == group.id
            ).count()

        return groups

    @staticmethod
    def get_group_by_id(db: Session, user_id: int, group_id: int) -> Optional[Group]:
        """
        根据ID获取分组

        Args:
            db: 数据库会话
            user_id: 用户ID
            group_id: 分组ID

        Returns:
            分组对象，不存在返回None
        """
        return db.query(Group).filter(
            Group.id == group_id,
            Group.user_id == user_id
        ).first()

    @staticmethod
    def update_group(db: Session, user_id: int, group_id: int, group_data: GroupUpdate) -> Group:
        """
        更新分组

        Args:
            db: 数据库会话
            user_id: 用户ID
            group_id: 分组ID
            group_data: 更新数据

        Returns:
            更新后的分组对象

        Raises:
            ValueError: 分组不存在或名称重复
        """
        group = GroupService.get_group_by_id(db, user_id, group_id)

        if not group:
            raise ValueError("分组不存在")

        # 检查名称是否重复
        if group_data.name is not None and group_data.name != group.name:
            existing = db.query(Group).filter(
                Group.user_id == user_id,
                Group.name == group_data.name,
                Group.id != group_id
            ).first()

            if existing:
                raise ValueError("分组名称已存在")

            group.name = group_data.name

        if group_data.sort_order is not None:
            group.sort_order = group_data.sort_order

        db.commit()
        db.refresh(group)

        return group

    @staticmethod
    def delete_group(db: Session, user_id: int, group_id: int) -> bool:
        """
        删除分组

        Args:
            db: 数据库会话
            user_id: 用户ID
            group_id: 分组ID

        Returns:
            是否删除成功

        Raises:
            ValueError: 分组不存在
        """
        group = GroupService.get_group_by_id(db, user_id, group_id)

        if not group:
            raise ValueError("分组不存在")

        # 将该分组下的标的移到未分组
        db.query(Stock).filter(
            Stock.group_id == group_id
        ).update({"group_id": None})

        db.delete(group)
        db.commit()

        return True
