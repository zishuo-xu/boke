from typing import List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.alert import Alert, AlertNotification
from app.models.stock import Stock
from app.schemas.alert import AlertCreate, AlertUpdate
from app.services.market_service import market_service
import logging

logger = logging.getLogger(__name__)


class AlertService:
    """预警服务"""

    @staticmethod
    def create_alert(db: Session, user_id: int, alert_data: AlertCreate) -> Alert:
        """
        创建预警

        Args:
            db: 数据库会话
            user_id: 用户ID
            alert_data: 预警数据

        Returns:
            创建的预警对象

        Raises:
            ValueError: 标的不存在或类型不匹配
        """
        # 检查标的是否存在
        stock = db.query(Stock).filter(
            Stock.id == alert_data.stock_id,
            Stock.user_id == user_id
        ).first()

        if not stock:
            raise ValueError("标的不存在")

        # 创建预警
        db_alert = Alert(
            user_id=user_id,
            stock_id=alert_data.stock_id,
            alert_type=alert_data.alert_type,
            threshold=alert_data.threshold,
            enabled=True
        )

        db.add(db_alert)
        db.commit()
        db.refresh(db_alert)

        return db_alert

    @staticmethod
    def get_alerts(db: Session, user_id: int) -> List[Alert]:
        """
        获取用户的所有预警

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            预警列表
        """
        return db.query(Alert).filter(Alert.user_id == user_id).order_by(Alert.created_at.desc()).all()

    @staticmethod
    def get_alert_by_id(db: Session, user_id: int, alert_id: int):
        """
        根据ID获取预警

        Args:
            db: 数据库会话
            user_id: 用户ID
            alert_id: 预警ID

        Returns:
            预警对象，不存在返回None
        """
        return db.query(Alert).filter(
            Alert.id == alert_id,
            Alert.user_id == user_id
        ).first()

    @staticmethod
    def update_alert(db: Session, user_id: int, alert_id: int, alert_data: AlertUpdate) -> Alert:
        """
        更新预警

        Args:
            db: 数据库会话
            user_id: 用户ID
            alert_id: 预警ID
            alert_data: 更新数据

        Returns:
            更新后的预警对象

        Raises:
            ValueError: 预警不存在
        """
        alert = AlertService.get_alert_by_id(db, user_id, alert_id)

        if not alert:
            raise ValueError("预警不存在")

        # 更新字段
        if alert_data.threshold is not None:
            alert.threshold = alert_data.threshold

        if alert_data.enabled is not None:
            alert.enabled = alert_data.enabled

        db.commit()
        db.refresh(alert)

        return alert

    @staticmethod
    def delete_alert(db: Session, user_id: int, alert_id: int) -> bool:
        """
        删除预警

        Args:
            db: 数据库会话
            user_id: 用户ID
            alert_id: 预警ID

        Returns:
            是否删除成功

        Raises:
            ValueError: 预警不存在
        """
        alert = AlertService.get_alert_by_id(db, user_id, alert_id)

        if not alert:
            raise ValueError("预警不存在")

        db.delete(alert)
        db.commit()

        return True

    @staticmethod
    def get_notifications(db: Session, user_id: int, unread_only: bool = False) -> List[AlertNotification]:
        """
        获取通知列表

        Args:
            db: 数据库会话
            user_id: 用户ID
            unread_only: 是否只获取未读通知

        Returns:
            通知列表
        """
        query = db.query(AlertNotification).filter(AlertNotification.user_id == user_id)

        if unread_only:
            query = query.filter(AlertNotification.is_read == False)

        return query.order_by(AlertNotification.created_at.desc()).all()

    @staticmethod
    def mark_notification_read(db: Session, user_id: int, notification_id: int) -> bool:
        """
        标记通知为已读

        Args:
            db: 数据库会话
            user_id: 用户ID
            notification_id: 通知ID

        Returns:
            是否标记成功
        """
        notification = db.query(AlertNotification).filter(
            AlertNotification.id == notification_id,
            AlertNotification.user_id == user_id
        ).first()

        if not notification:
            return False

        notification.is_read = True
        db.commit()

        return True

    @staticmethod
    async def check_all_alerts(db: Session):
        """
        检查所有启用的预警

        这个方法由定时任务调用
        """
        # 获取所有启用的预警
        alerts = db.query(Alert).filter(Alert.enabled == True).all()

        for alert in alerts:
            try:
                await AlertService._check_alert(db, alert)
            except Exception as e:
                logger.error(f"检查预警{alert.id}失败: {e}")

    @staticmethod
    async def _check_alert(db: Session, alert: Alert):
        """
        检查单个预警

        Args:
            db: 数据库会话
            alert: 预警对象
        """
        # 获取标的实时数据
        data = market_service.get_stock_realtime(db, alert.user_id, alert.stock_id, force_refresh=True)

        if not data:
            logger.warning(f"无法获取标的{alert.stock_id}的实时数据")
            return

        # 判断是否触发预警
        current_price = data['price']
        is_triggered = False

        if alert.alert_type == 'upper' and current_price >= alert.threshold:
            is_triggered = True
        elif alert.alert_type == 'lower' and current_price <= alert.threshold:
            is_triggered = True

        if not is_triggered:
            return

        # 检查是否1小时内已触发过
        if alert.triggered_at:
            time_diff = datetime.now() - alert.triggered_at
            if time_diff < timedelta(hours=1):
                logger.info(f"预警{alert.id}1小时内已触发过，跳过")
                return

        # 触发预警
        AlertService._trigger_alert(db, alert, current_price)

    @staticmethod
    def _trigger_alert(db: Session, alert: Alert, current_price: float):
        """
        触发预警

        Args:
            db: 数据库会话
            alert: 预警对象
            current_price: 当前价格
        """
        # 更新预警触发时间
        alert.triggered_at = datetime.now()
        db.commit()

        # 创建通知
        stock = db.query(Stock).filter(Stock.id == alert.stock_id).first()
        if not stock:
            return

        alert_type_text = "上限" if alert.alert_type == 'upper' else "下限"
        message = f"【价格预警】{stock.name}({stock.code})当前价格{current_price:.2f}，达到{alert_type_text}预警阈值{alert.threshold:.2f}"

        notification = AlertNotification(
            user_id=alert.user_id,
            alert_id=alert.id,
            message=message
        )

        db.add(notification)
        db.commit()

        logger.info(f"预警{alert.id}已触发: {message}")
