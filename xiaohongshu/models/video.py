"""视频相关操作模块"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from models.database import get_connection
from utils.constants import REQUIRED_TIME_POINTS


def add_video(blogger_id: int, title: str, video_link: str,
               publish_time: datetime, tags: str = None) -> int:
    """新增视频

    Args:
        blogger_id: 博主ID
        title: 视频标题
        video_link: 视频链接
        publish_time: 发布时间
        tags: 标签（字符串）

    Returns:
        新增视频的ID
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO videos (blogger_id, title, video_link, publish_time, tags)
           VALUES (?, ?, ?, ?, ?)""",
        (blogger_id, title, video_link, publish_time.isoformat(), tags)
    )
    video_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return video_id


def get_videos_by_blogger(blogger_id: int) -> List[Dict[str, Any]]:
    """获取指定博主的所有视频

    Args:
        blogger_id: 博主ID

    Returns:
        视频列表
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM videos WHERE blogger_id = ? ORDER BY publish_time DESC",
        (blogger_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_video_by_id(video_id: int) -> Optional[Dict[str, Any]]:
    """根据ID获取视频

    Args:
        video_id: 视频ID

    Returns:
        视频信息，如果不存在则返回None
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def update_video(video_id: int, title: str = None, video_link: str = None,
                 publish_time: datetime = None, tags: str = None) -> bool:
    """更新视频信息

    Args:
        video_id: 视频ID
        title: 视频标题
        video_link: 视频链接
        publish_time: 发布时间
        tags: 标签

    Returns:
        是否更新成功
    """
    updates = []
    params = []

    if title is not None:
        updates.append("title = ?")
        params.append(title)

    if video_link is not None:
        updates.append("video_link = ?")
        params.append(video_link)

    if publish_time is not None:
        updates.append("publish_time = ?")
        params.append(publish_time.isoformat())

    if tags is not None:
        updates.append("tags = ?")
        params.append(tags)

    if not updates:
        return False

    params.append(video_id)
    sql = f"UPDATE videos SET {', '.join(updates)} WHERE id = ?"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    return affected > 0


def delete_video(video_id: int) -> bool:
    """删除视频

    Args:
        video_id: 视频ID

    Returns:
        是否删除成功
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    return affected > 0


def search_videos(blogger_id: int, keyword: str) -> List[Dict[str, Any]]:
    """搜索视频

    Args:
        blogger_id: 博主ID
        keyword: 搜索关键词（匹配标题或链接）

    Returns:
        匹配的视频列表
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT * FROM videos
           WHERE blogger_id = ? AND (title LIKE ? OR video_link LIKE ?)
           ORDER BY publish_time DESC""",
        (blogger_id, f"%{keyword}%", f"%{keyword}%")
    )
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def filter_videos_by_date(blogger_id: int, start_date: datetime,
                           end_date: datetime) -> List[Dict[str, Any]]:
    """按时间段筛选视频

    Args:
        blogger_id: 博主ID
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        符合条件的视频列表
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT * FROM videos
           WHERE blogger_id = ? AND publish_time BETWEEN ? AND ?
           ORDER BY publish_time DESC""",
        (blogger_id, start_date.isoformat(), end_date.isoformat())
    )
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def filter_videos_by_performance(blogger_id: int, filter_type: str,
                                  high_threshold: int, low_threshold: int) -> List[Dict[str, Any]]:
    """按流量表现筛选视频

    Args:
        blogger_id: 博主ID
        filter_type: 筛选类型（all/high/low）
        high_threshold: 爆款阈值（播放量）
        low_threshold: 低流量阈值（播放量）

    Returns:
        符合条件的视频列表
    """
    conn = get_connection()
    cursor = conn.cursor()

    if filter_type == "all":
        cursor.execute(
            "SELECT * FROM videos WHERE blogger_id = ? ORDER BY publish_time DESC",
            (blogger_id,)
        )
    elif filter_type == "high":
        # 获取1小时播放量大于阈值的视频
        cursor.execute(
            """SELECT v.* FROM videos v
               JOIN video_metrics m ON v.id = m.video_id
               WHERE v.blogger_id = ? AND m.time_point = 1 AND m.play_count >= ?
               ORDER BY v.publish_time DESC""",
            (blogger_id, high_threshold)
        )
    elif filter_type == "low":
        # 获取1小时播放量小于阈值的视频
        cursor.execute(
            """SELECT v.* FROM videos v
               JOIN video_metrics m ON v.id = m.video_id
               WHERE v.blogger_id = ? AND m.time_point = 1 AND m.play_count < ?
               ORDER BY v.publish_time DESC""",
            (blogger_id, low_threshold)
        )
    else:
        cursor.execute(
            "SELECT * FROM videos WHERE blogger_id = ? ORDER BY publish_time DESC",
            (blogger_id,)
        )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_videos_with_required_metrics(blogger_id: int) -> List[Dict[str, Any]]:
    """获取已录完必录数据（1h/4h/8h）的视频

    Args:
        blogger_id: 博主ID

    Returns:
        视频列表（包含必录数据）
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT v.* FROM videos v
           WHERE v.blogger_id = ? AND (
               SELECT COUNT(*) FROM video_metrics m
               WHERE m.video_id = v.id AND m.time_point IN (1, 4, 8)
           ) >= 3
           ORDER BY v.publish_time DESC""",
        (blogger_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]
