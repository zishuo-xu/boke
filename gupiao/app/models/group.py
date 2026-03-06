from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Group(Base, TimestampMixin):
    """分组表"""

    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="groups")
    stocks: Mapped[list["Stock"]] = relationship(
        "Stock", back_populates="group", cascade="all, delete-orphan"
    )
