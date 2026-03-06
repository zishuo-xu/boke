from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password, create_access_token


class UserService:
    """用户服务"""

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """
        创建用户

        Args:
            db: 数据库会话
            user_data: 用户创建数据

        Returns:
            创建的用户对象

        Raises:
            ValueError: 邮箱已存在
        """
        # 检查邮箱是否已存在
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValueError("邮箱已被注册")

        # 创建新用户
        db_user = User(
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            nickname=user_data.nickname or user_data.email.split("@")[0]
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return db_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """
        验证用户登录

        Args:
            db: 数据库会话
            email: 邮箱
            password: 密码

        Returns:
            用户对象，验证失败返回None
        """
        user = db.query(User).filter(User.email == email).first()

        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    @staticmethod
    def login_user(db: Session, email: str, password: str) -> Optional[tuple[User, str]]:
        """
        用户登录

        Args:
            db: 数据库会话
            email: 邮箱
            password: 密码

        Returns:
            (用户对象, 访问令牌)，验证失败返回None
        """
        user = UserService.authenticate_user(db, email, password)

        if not user:
            return None

        # 创建访问令牌
        access_token = create_access_token(data={"sub": str(user.id)})

        return user, access_token

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        根据ID获取用户

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            用户对象，不存在返回None
        """
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        根据邮箱获取用户

        Args:
            db: 数据库会话
            email: 邮箱

        Returns:
            用户对象，不存在返回None
        """
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def update_user(db: Session, user: User, nickname: Optional[str] = None) -> User:
        """
        更新用户信息

        Args:
            db: 数据库会话
            user: 用户对象
            nickname: 昵称

        Returns:
            更新后的用户对象
        """
        if nickname is not None:
            user.nickname = nickname

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def delete_user(db: Session, user: User) -> bool:
        """
        删除用户

        Args:
            db: 数据库会话
            user: 用户对象

        Returns:
            是否删除成功
        """
        db.delete(user)
        db.commit()

        return True
