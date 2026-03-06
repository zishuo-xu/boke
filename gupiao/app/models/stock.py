from sqlalchemy import String, Integer, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Stock(Base, TimestampMixin):
    """标的表（股票/基金）"""

    __tablename__ = "stocks"
    __table_args__ = (
        CheckConstraint("type IN ('stock', 'fund')", name="check_stock_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'stock' 或 'fund'

    # 股票特有字段
    market: Mapped[str] = mapped_column(String(10), nullable=True)  # 'A股', '港股', '美股'
    sector: Mapped[str] = mapped_column(String(50), nullable=True)  # 所属板块

    # 基金特有字段
    fund_company: Mapped[str] = mapped_column(String(100), nullable=True)  # 基金公司
    fund_type: Mapped[str] = mapped_column(String(50), nullable=True)  # 基金类型

    # 分组和排序
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="stocks")
    group: Mapped["Group"] = relationship("Group", back_populates="stocks")
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="stock", cascade="all, delete-orphan"
    )
