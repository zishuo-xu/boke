from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.stock import Stock
from app.models.alert import Alert
from app.schemas.alert import AlertCreate, AlertUpdate, AlertResponse, NotificationResponse
from app.services.alert_service import AlertService

router = APIRouter()


# ========== 预警管理 API ==========

@router.post("", response_model=AlertResponse, status_code=201)
def create_alert(
    alert_data: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建预警

    - **stock_id**: 标的ID
    - **alert_type**: 预警类型（upper=上限, lower=下限）
    - **threshold**: 预警阈值
    """
    try:
        alert = AlertService.create_alert(db, current_user.id, alert_data)
        return alert
    except ValueError as e:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[AlertResponse])
def get_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取预警列表

    返回所有预警
    """
    # 获取所有预警
    alerts = AlertService.get_alerts(db, current_user.id)

    # 添加标的信息
    result = []
    for alert in alerts:
        stock = db.query(Stock).filter(Stock.id == alert.stock_id).first()
        result.append({
            **AlertResponse.model_validate(alert).model_dump(),
            "stock_code": stock.code if stock else "",
            "stock_name": stock.name if stock else "",
        })

    return result


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取单个预警详情
    """
    alert = AlertService.get_alert_by_id(db, current_user.id, alert_id)

    if not alert:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="预警不存在"
        )

    return alert


@router.put("/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int,
    alert_data: AlertUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新预警

    - **threshold**: 预警阈值（可选）
    - **enabled**: 是否启用（可选）
    """
    try:
        alert = AlertService.update_alert(db, current_user.id, alert_id, alert_data)
        return alert
    except ValueError as e:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{alert_id}")
def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除预警
    """
    try:
        AlertService.delete_alert(db, current_user.id, alert_id)
        return {"message": "删除成功"}
    except ValueError as e:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ========== 通知管理 API ==========

@router.get("/notifications", response_model=List[NotificationResponse])
def get_notifications(
    unread_only: bool = Query(False, description="是否只获取未读通知"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取通知列表

    - **unread_only**: 是否只获取未读通知
    """
    notifications = AlertService.get_notifications(db, current_user.id, unread_only)

    # 添加预警信息
    result = []
    for notification in notifications:
        alert = db.query(Alert).filter(Alert.id == notification.alert_id).first()
        stock = db.query(Stock).filter(Stock.id == alert.stock_id).first() if alert else None

        result.append({
            **NotificationResponse.model_validate(notification).model_dump(),
            "stock_code": stock.code if stock else "",
            "stock_name": stock.name if stock else "",
            "alert_type": alert.alert_type if alert else "",
        })

    return result


@router.put("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    标记通知为已读
    """
    success = AlertService.mark_notification_read(db, current_user.id, notification_id)

    if not success:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在"
        )

    return {"message": "标记成功"}
