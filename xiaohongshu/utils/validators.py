"""数据验证模块"""
from typing import Tuple, Optional


def validate_nickname(nickname: str) -> Tuple[bool, Optional[str]]:
    """验证博主昵称

    Args:
        nickname: 博主昵称

    Returns:
        (是否有效, 错误信息)
    """
    if not nickname or not nickname.strip():
        return False, "博主昵称不能为空"

    if len(nickname) > 20:
        return False, "博主昵称不能超过20个字符"

    return True, None


def validate_video_title(title: str) -> Tuple[bool, Optional[str]]:
    """验证视频标题

    Args:
        title: 视频标题

    Returns:
        (是否有效, 错误信息)
    """
    if not title or not title.strip():
        return False, "视频标题不能为空"

    if len(title) > 50:
        return False, "视频标题不能超过50个字符"

    return True, None


def validate_video_link(link: str) -> Tuple[bool, Optional[str]]:
    """验证视频链接

    Args:
        link: 视频链接

    Returns:
        (是否有效, 错误信息)
    """
    if not link or not link.strip():
        return False, "视频链接不能为空"

    if "xiaohongshu.com" not in link.lower():
        return False, "请输入有效的小红书链接"

    return True, None


def validate_positive_integer(value: str, field_name: str) -> Tuple[bool, Optional[int], Optional[str]]:
    """验证非负整数

    Args:
        value: 字符串值
        field_name: 字段名称

    Returns:
        (是否有效, 转换后的整数, 错误信息)
    """
    if not value or not value.strip():
        return False, 0, f"{field_name}不能为空"

    try:
        num = int(value)
        if num < 0:
            return False, 0, f"{field_name}不能为负数"
        return True, num, None
    except ValueError:
        return False, 0, f"{field_name}必须是整数"


def validate_completion_rate(value: str) -> Tuple[bool, Optional[float], Optional[str]]:
    """验证完播率

    Args:
        value: 字符串值

    Returns:
        (是否有效, 转换后的浮点数, 错误信息)
    """
    if not value or not value.strip():
        return False, 0.0, "完播率不能为空"

    try:
        rate = float(value)
        if rate < 0 or rate > 100:
            return False, 0.0, "完播率必须在0-100之间"
        return True, rate, None
    except ValueError:
        return False, 0.0, "完播率必须是数字"


def validate_metrics_data(play_count: str, like_count: str, collect_count: str,
                          comment_count: str, completion_rate: str) -> Tuple[bool, Optional[str], dict]:
    """验证流量数据

    Args:
        play_count: 播放量字符串
        like_count: 点赞数字符串
        collect_count: 收藏数字符串
        comment_count: 评论数字符串
        completion_rate: 完播率字符串

    Returns:
        (是否有效, 错误信息, 验证后的数据字典)
    """
    data = {}

    # 验证播放量
    valid, num, error = validate_positive_integer(play_count, "播放量")
    if not valid:
        return False, error, data
    data['play_count'] = num

    # 验证点赞数
    valid, num, error = validate_positive_integer(like_count, "点赞数")
    if not valid:
        return False, error, data
    data['like_count'] = num

    # 验证收藏数
    valid, num, error = validate_positive_integer(collect_count, "收藏数")
    if not valid:
        return False, error, data
    data['collect_count'] = num

    # 验证评论数
    valid, num, error = validate_positive_integer(comment_count, "评论数")
    if not valid:
        return False, error, data
    data['comment_count'] = num

    # 验证完播率
    valid, rate, error = validate_completion_rate(completion_rate)
    if not valid:
        return False, error, data
    data['completion_rate'] = rate

    return True, None, data
