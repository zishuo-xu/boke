"""数据库连接和初始化模块"""
import sqlite3
from pathlib import Path
from utils.constants import DATABASE_FILE


def get_db_path():
    """获取数据库文件路径"""
    # 确保在项目根目录下创建数据库
    project_root = Path(__file__).parent.parent
    return project_root / DATABASE_FILE


def get_connection():
    """获取数据库连接"""
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # 允许通过列名访问
    return conn


def init_database():
    """初始化数据库表结构"""
    conn = get_connection()
    cursor = conn.cursor()

    # 创建博主表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bloggers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname VARCHAR(20) NOT NULL,
            account_link TEXT,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建视频表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blogger_id INTEGER NOT NULL,
            title VARCHAR(50) NOT NULL,
            video_link TEXT NOT NULL,
            publish_time TIMESTAMP NOT NULL,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (blogger_id) REFERENCES bloggers(id) ON DELETE CASCADE
        )
    """)

    # 创建流量数据表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS video_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            time_point INTEGER NOT NULL,
            play_count INTEGER NOT NULL,
            like_count INTEGER NOT NULL,
            collect_count INTEGER NOT NULL,
            comment_count INTEGER NOT NULL,
            completion_rate DECIMAL(4,1) NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
            UNIQUE(video_id, time_point)
        )
    """)

    # 创建索引以提高查询性能
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_videos_blogger_id
        ON videos(blogger_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_videos_publish_time
        ON videos(publish_time)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_metrics_video_id
        ON video_metrics(video_id)
    """)

    conn.commit()
    conn.close()


# 应用启动时初始化数据库
init_database()
