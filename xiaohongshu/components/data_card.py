"""数据卡片组件"""
import streamlit as st
import pandas as pd
from typing import Dict, Any, List


def render_data_card(video: Dict[str, Any], blogger: Dict[str, Any]):
    """渲染单视频数据卡片

    Args:
        video: 视频信息
        blogger: 博主信息
    """
    from models.metrics import get_metrics_by_video
    from datetime import datetime

    st.subheader("📊 视频数据卡片")

    # 视频基础信息
    with st.container(border=True):
        st.write("### 基本信息")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.write("**博主**")
            st.write(blogger['nickname'])

        with col2:
            st.write("**标题**")
            st.write(video['title'])

        with col3:
            pub_time = datetime.fromisoformat(video['publish_time'])
            st.write("**发布时间**")
            st.write(pub_time.strftime('%Y-%m-%d %H:%M'))

        if video['tags']:
            st.write("**标签**")
            st.write(video['tags'])

        if video['video_link']:
            st.markdown(f"[📹 视频链接]({video['video_link']})")

    # 流量数据表格
    metrics = get_metrics_by_video(video['id'])

    if metrics:
        st.divider()
        st.write("### 流量数据")

        # 构建表格数据
        data = []
        for m in metrics:
            data.append({
                '时间节点': f"{m['time_point']}h",
                '播放量': m['play_count'],
                '点赞数': m['like_count'],
                '收藏数': m['collect_count'],
                '评论数': m['comment_count'],
                '完播率(%)': m['completion_rate']
            })

        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)


def render_metrics_chart(video: Dict[str, Any]):
    """渲染流量曲线图

    Args:
        video: 视频信息
    """
    from models.metrics import get_metrics_by_video
    from utils.constants import METRICS

    metrics = get_metrics_by_video(video['id'])

    if not metrics:
        st.info("暂无流量数据，请先录入数据")
        return

    # 构建图表数据
    metrics_dict = {}
    for m in metrics:
        time_point = m['time_point']
        metrics_dict[time_point] = m

    # 按时间节点排序
    sorted_time_points = sorted(metrics_dict.keys())

    # 选择要显示的指标
    selected_metrics = st.multiselect(
        "选择要显示的指标",
        options=list(METRICS.keys()),
        format_func=lambda x: METRICS[x],
        default=['play_count', 'like_count']
    )

    if not selected_metrics:
        st.warning("请至少选择一个指标")
        return

    # 构建图表数据
    chart_data = {'时间节点': [f"{tp}h" for tp in sorted_time_points]}
    for metric in selected_metrics:
        chart_data[METRICS[metric]] = [
            metrics_dict[tp][metric] for tp in sorted_time_points
        ]

    df = pd.DataFrame(chart_data)
    df = df.set_index('时间节点')

    # 显示折线图
    st.line_chart(df, use_container_width=True)

    # 显示数据增长分析
    if len(sorted_time_points) >= 2:
        st.divider()
        st.write("### 📈 增长分析")

        for metric in selected_metrics:
            if metric == 'completion_rate':
                continue  # 跳过完播率的增长分析

            first_value = metrics_dict[sorted_time_points[0]][metric]
            last_value = metrics_dict[sorted_time_points[-1]][metric]

            if first_value > 0:
                growth_rate = ((last_value - first_value) / first_value) * 100
                growth_text = f"{growth_rate:+.1f}%"
            else:
                growth_text = "N/A"

            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**{METRICS[metric]}**")
            with col2:
                st.write(f"{sorted_time_points[0]}h: {first_value}")
            with col3:
                st.write(f"{sorted_time_points[-1]}h: {last_value} (增长: {growth_text})")
