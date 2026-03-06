"""博主相关操作模块"""
from typing import List, Optional, Dict, Any
from models.database import get_connection


def add_blogger(nickname: str, account_link: str = None, note: str = None) -> int:
    """新增博主

    Args:
        nickname: 博主昵称
        account_link: 小红书账号链接
        note: 备注

    Returns:
        新增博主的ID
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO bloggers (nickname, account_link, note) VALUES (?, ?, ?)",
        (nickname, account_link, note)
    )
    blogger_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return blogger_id


def get_all_bloggers() -> List[Dict[str, Any]]:
    """获取所有博主

    Returns:
        博主列表
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bloggers ORDER BY id")
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_blogger_by_id(blogger_id: int) -> Optional[Dict[str, Any]]:
    """根据ID获取博主

    Args:
        blogger_id: 博主ID

    Returns:
        博主信息，如果不存在则返回None
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bloggers WHERE id = ?", (blogger_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def update_blogger(blogger_id: int, nickname: str = None,
                  account_link: str = None, note: str = None) -> bool:
    """更新博主信息

    Args:
        blogger_id: 博主ID
        nickname: 博主昵称
        account_link: 小红书账号链接
        note: 备注

    Returns:
        是否更新成功
    """
    # 构建更新语句
    updates = []
    params = []

    if nickname is not None:
        updates.append("nickname = ?")
        params.append(nickname)

    if account_link is not None:
        updates.append("account_link = ?")
        params.append(account_link)

    if note is not None:
        updates.append("note = ?")
        params.append(note)

    if not updates:
        return False

    params.append(blogger_id)
    sql = f"UPDATE bloggers SET {', '.join(updates)} WHERE id = ?"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    return affected > 0


def delete_blogger(blogger_id: int) -> bool:
    """删除博主

    Args:
        blogger_id: 博主ID

    Returns:
        是否删除成功
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bloggers WHERE id = ?", (blogger_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    return affected > 0


def get_blogger_video_count(blogger_id: int) -> int:
    """获取博主的视频数量

    Args:
        blogger_id: 博主ID

    Returns:
        视频数量
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM videos WHERE blogger_id = ?", (blogger_id,))
    count = cursor.fetchone()[0]
    conn.close()

    return count
