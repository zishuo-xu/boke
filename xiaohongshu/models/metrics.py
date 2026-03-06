"""流量数据相关操作模块"""
from typing import List, Optional, Dict, Any
from models.database import get_connection
from utils.constants import TIME_POINTS


def add_metrics(video_id: int, time_point: int, play_count: int,
                like_count: int, collect_count: int, comment_count: int,
                completion_rate: float) -> int:
    """新增流量数据

    Args:
        video_id: 视频ID
        time_point: 时间节点（1/4/8/24小时）
        play_count: 播放量
        like_count: 点赞数
        collect_count: 收藏数
        comment_count: 评论数
        completion_rate: 完播率（百分比）

    Returns:
        新增数据的ID
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO video_metrics
           (video_id, time_point, play_count, like_count, collect_count, comment_count, completion_rate)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (video_id, time_point, play_count, like_count, collect_count, comment_count, completion_rate)
    )
    metrics_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return metrics_id


def get_metrics_by_video(video_id: int) -> List[Dict[str, Any]]:
    """获取指定视频的所有流量数据

    Args:
        video_id: 视频ID

    Returns:
        流量数据列表，按时间节点排序
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM video_metrics WHERE video_id = ? ORDER BY time_point",
        (video_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_metrics_by_video_and_time_point(video_id: int, time_point: int) -> Optional[Dict[str, Any]]:
    """获取指定视频在某个时间节点的流量数据

    Args:
        video_id: 视频ID
        time_point: 时间节点（1/4/8/24小时）

    Returns:
        流量数据，如果不存在则返回None
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM video_metrics WHERE video_id = ? AND time_point = ?",
        (video_id, time_point)
    )
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def update_metrics(metrics_id: int, play_count: int = None, like_count: int = None,
                   collect_count: int = None, comment_count: int = None,
                   completion_rate: float = None) -> bool:
    """更新流量数据

    Args:
        metrics_id: 流量数据ID
        play_count: 播放量
        like_count: 点赞数
        collect_count: 收藏数
        comment_count: 评论数
        completion_rate: 完播率（百分比）

    Returns:
        是否更新成功
    """
    updates = []
    params = []

    if play_count is not None:
        updates.append("play_count = ?")
        params.append(play_count)

    if like_count is not None:
        updates.append("like_count = ?")
        params.append(like_count)

    if collect_count is not None:
        updates.append("collect_count = ?")
        params.append(collect_count)

    if comment_count is not None:
        updates.append("comment_count = ?")
        params.append(comment_count)

    if completion_rate is not None:
        updates.append("completion_rate = ?")
        params.append(completion_rate)

    if not updates:
        return False

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(metrics_id)
    sql = f"UPDATE video_metrics SET {', '.join(updates)} WHERE id = ?"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    return affected > 0


def upsert_metrics(video_id: int, time_point: int, play_count: int,
                   like_count: int, collect_count: int, comment_count: int,
                   completion_rate: float) -> bool:
    """新增或更新流量数据

    Args:
        video_id: 视频ID
        time_point: 时间节点（1/4/8/24小时）
        play_count: 播放量
        like_count: 点赞数
        collect_count: 收藏数
        comment_count: 评论数
        completion_rate: 完播率（百分比）

    Returns:
        是否成功
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 检查是否已存在该时间节点的数据
    existing = get_metrics_by_video_and_time_point(video_id, time_point)

    if existing:
        # 更新
        cursor.execute(
            """UPDATE video_metrics
               SET play_count = ?, like_count = ?, collect_count = ?, comment_count = ?,
                   completion_rate = ?, updated_at = CURRENT_TIMESTAMP
               WHERE video_id = ? AND time_point = ?""",
            (play_count, like_count, collect_count, comment_count, completion_rate, video_id, time_point)
        )
    else:
        # 新增
        cursor.execute(
            """INSERT INTO video_metrics
               (video_id, time_point, play_count, like_count, collect_count, comment_count, completion_rate)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (video_id, time_point, play_count, like_count, collect_count, comment_count, completion_rate)
        )

    conn.commit()
    conn.close()
    return True


def delete_metrics_by_video(video_id: int) -> bool:
    """删除指定视频的所有流量数据

    Args:
        video_id: 视频ID

    Returns:
        是否删除成功
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM video_metrics WHERE video_id = ?", (video_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    return affected > 0


def get_videos_summary_metrics(video_ids: List[int]) -> Dict[int, Dict[int, Dict[str, Any]]]:
    """批量获取多个视频的流量数据

    Args:
        video_ids: 视频ID列表

    Returns:
        字典，key为video_id，value为该视频的流量数据（key为time_point）
    """
    if not video_ids:
        return {}

    conn = get_connection()
    cursor = conn.cursor()

    placeholders = ','.join('?' * len(video_ids))
    cursor.execute(
        f"SELECT * FROM video_metrics WHERE video_id IN ({placeholders}) ORDER BY video_id, time_point",
        video_ids
    )
    rows = cursor.fetchall()
    conn.close()

    result = {}
    for row in rows:
        row_dict = dict(row)
        video_id = row_dict['video_id']
        time_point = row_dict['time_point']

        if video_id not in result:
            result[video_id] = {}

        result[video_id][time_point] = row_dict

    return result


def get_metric_trend(video_id: int, metric_name: str) -> Dict[int, float]:
    """获取指定视频某个指标的完整趋势

    Args:
        video_id: 视频ID
        metric_name: 指标名称（play_count, like_count, collect_count, comment_count, completion_rate）

    Returns:
        字典，key为time_point，value为指标值
    """
    metrics = get_metrics_by_video(video_id)

    # 只返回已录入的时间节点
    return {m['time_point']: m[metric_name] for m in metrics}
