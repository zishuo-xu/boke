from sqlalchemy import String, Integer, ForeignKey, Boolean, Numeric, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Alert(Base, TimestampMixin):
    """预警表"""

    __tablename__ = "alerts"
    __table_args__ = (
        CheckConstraint("alert_type IN ('upper', 'lower')", name="check_alert_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False
    )
    alert_type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'upper' 上限, 'lower' 下限
    threshold: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)  # 预警阈值
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)  # 是否启用
    triggered_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)  # 最后触发时间

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="alerts")
    stock: Mapped["Stock"] = relationship("Stock", back_populates="alerts")
    notifications: Mapped[list["AlertNotification"]] = relationship(
        "AlertNotification", back_populates="alert", cascade="all, delete-orphan"
    )


class AlertNotification(Base, TimestampMixin):
    """预警通知表"""

    __tablename__ = "alert_notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    alert_id: Mapped[int] = mapped_column(
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False
    )
    message: Mapped[str] = mapped_column(String(500), nullable=False)  # 通知内容
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否已读

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="notifications")
    alert: Mapped["Alert"] = relationship("Alert", back_populates="notifications")
