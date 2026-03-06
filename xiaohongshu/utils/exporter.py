"""数据导出模块"""
from typing import List, Dict, Any
import pandas as pd
from io import BytesIO


def export_videos_to_excel(videos_data: List[Dict[str, Any]]) -> BytesIO:
    """导出视频数据为Excel格式

    Args:
        videos_data: 视频数据列表

    Returns:
        Excel文件的字节流
    """
    # 构建导出数据
    export_rows = []

    for video in videos_data:
        base_info = {
            '博主ID': video.get('blogger_id'),
            '博主昵称': video.get('blogger_nickname', ''),
            '视频ID': video['id'],
            '视频标题': video['title'],
            '视频链接': video['video_link'],
            '发布时间': video['publish_time'],
            '标签': video.get('tags', ''),
        }

        # 获取该视频的所有时间节点数据
        metrics = video.get('metrics', {})

        # 按时间节点添加数据
        for time_point in [1, 4, 8, 24]:
            if time_point in metrics:
                m = metrics[time_point]
                prefix = f'{time_point}h'
                base_info.update({
                    f'{prefix}_播放量': m['play_count'],
                    f'{prefix}_点赞数': m['like_count'],
                    f'{prefix}_收藏数': m['collect_count'],
                    f'{prefix}_评论数': m['comment_count'],
                    f'{prefix}_完播率(%)': m['completion_rate'],
                })
            else:
                prefix = f'{time_point}h'
                base_info.update({
                    f'{prefix}_播放量': '',
                    f'{prefix}_点赞数': '',
                    f'{prefix}_收藏数': '',
                    f'{prefix}_评论数': '',
                    f'{prefix}_完播率(%)': '',
                })

        export_rows.append(base_info)

    # 创建DataFrame
    df = pd.DataFrame(export_rows)

    # 创建Excel文件
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='视频数据')
        # 调整列宽
        worksheet = writer.sheets['视频数据']
        for idx, col in enumerate(df.columns, 1):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(col)
            )
            worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 50)

    output.seek(0)
    return output


def export_videos_to_csv(videos_data: List[Dict[str, Any]]) -> BytesIO:
    """导出视频数据为CSV格式

    Args:
        videos_data: 视频数据列表

    Returns:
        CSV文件的字节流
    """
    # 构建导出数据（与Excel格式相同）
    export_rows = []

    for video in videos_data:
        base_info = {
            '博主ID': video.get('blogger_id'),
            '博主昵称': video.get('blogger_nickname', ''),
            '视频ID': video['id'],
            '视频标题': video['title'],
            '视频链接': video['video_link'],
            '发布时间': video['publish_time'],
            '标签': video.get('tags', ''),
        }

        # 获取该视频的所有时间节点数据
        metrics = video.get('metrics', {})

        # 按时间节点添加数据
        for time_point in [1, 4, 8, 24]:
            if time_point in metrics:
                m = metrics[time_point]
                prefix = f'{time_point}h'
                base_info.update({
                    f'{prefix}_播放量': m['play_count'],
                    f'{prefix}_点赞数': m['like_count'],
                    f'{prefix}_收藏数': m['collect_count'],
                    f'{prefix}_评论数': m['comment_count'],
                    f'{prefix}_完播率(%)': m['completion_rate'],
                })
            else:
                prefix = f'{time_point}h'
                base_info.update({
                    f'{prefix}_播放量': '',
                    f'{prefix}_点赞数': '',
                    f'{prefix}_收藏数': '',
                    f'{prefix}_评论数': '',
                    f'{prefix}_完播率(%)': '',
                })

        export_rows.append(base_info)

    # 创建DataFrame
    df = pd.DataFrame(export_rows)

    # 创建CSV文件
    output = BytesIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    return output
