"""导出对话框组件"""
import streamlit as st
from typing import List, Dict, Any
from utils.exporter import export_videos_to_excel, export_videos_to_csv


def render_export_dialog(blogger_id: int, blogger_nickname: str,
                         videos: List[Dict[str, Any]]):
    """渲染数据导出对话框

    Args:
        blogger_id: 博主ID
        blogger_nickname: 博主昵称
        videos: 视频列表
    """
    from models.metrics import get_videos_summary_metrics

    if not videos:
        st.info("暂无可导出的数据")
        return

    # 获取所有视频的流量数据
    video_ids = [v['id'] for v in videos]
    metrics_summary = get_videos_summary_metrics(video_ids)

    # 为每个视频添加博主昵称和流量数据
    export_data = []
    for video in videos:
        video['blogger_nickname'] = blogger_nickname
        video['metrics'] = metrics_summary.get(video['id'], {})
        export_data.append(video)

    # 选择导出范围
    export_scope = st.radio(
        "导出范围",
        ["当前博主所有视频", "选中的视频"],
        horizontal=True
    )

    selected_videos = []
    if export_scope == "当前博主所有视频":
        selected_videos = export_data
    else:
        # 多选视频
        video_options = {v['id']: f"{v['title']}" for v in export_data}
        selected_ids = st.multiselect(
            "选择要导出的视频",
            options=list(video_options.keys()),
            format_func=lambda x: video_options[x]
        )
        selected_videos = [v for v in export_data if v['id'] in selected_ids]

    if not selected_videos:
        st.warning("请先选择要导出的视频")
        return

    # 选择导出格式
    export_format = st.radio(
        "导出格式",
        ["Excel", "CSV"],
        horizontal=True
    )

    # 导出按钮
    if st.button("导出数据", type="primary", use_container_width=True):
        try:
            if export_format == "Excel":
                output = export_videos_to_excel(selected_videos)
                st.download_button(
                    label="下载Excel文件",
                    data=output,
                    file_name=f"{blogger_nickname}_视频数据.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                st.success("数据导出成功！请点击上方按钮下载文件。")
            else:  # CSV
                output = export_videos_to_csv(selected_videos)
                st.download_button(
                    label="下载CSV文件",
                    data=output,
                    file_name=f"{blogger_nickname}_视频数据.csv",
                    mime="text/csv"
                )
                st.success("数据导出成功！请点击上方按钮下载文件。")
        except Exception as e:
            st.error(f"导出失败：{str(e)}")

    # 显示导出预览
    st.divider()
    st.write("### 导出预览")

    preview_data = []
    for video in selected_videos[:5]:  # 只显示前5条
        base = {
            '视频标题': video['title'],
            '发布时间': video['publish_time'],
        }

        metrics = video.get('metrics', {})
        for time_point in [1, 4, 8, 24]:
            if time_point in metrics:
                m = metrics[time_point]
                base[f'{time_point}h_播放量'] = m['play_count']
                base[f'{time_point}h_点赞数'] = m['like_count']
            else:
                base[f'{time_point}h_播放量'] = ''
                base[f'{time_point}h_点赞数'] = ''

        preview_data.append(base)

    if preview_data:
        import pandas as pd
        df = pd.DataFrame(preview_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        if len(selected_videos) > 5:
            st.info(f"共{len(selected_videos)}条数据，仅显示前5条预览")
