"""数据录入页"""
import streamlit as st
from models.blogger import get_blogger_by_id
from models.video import get_video_by_id
from models.metrics import get_metrics_by_video, get_metrics_by_video_and_time_point, upsert_metrics
from utils.constants import REQUIRED_TIME_POINTS, OPTIONAL_TIME_POINTS
from utils.validators import validate_metrics_data
from datetime import datetime
import pandas as pd


def render_entry():
    """渲染数据录入页"""
    st.title("📝 数据录入")

    # 检查是否有选中的视频
    video_id = st.session_state.get('current_video_id')
    if not video_id:
        st.warning("请先选择一个视频")
        st.button("返回主页", on_click=lambda: st.session_state.update({'page': 'home', 'current_video_id': None}))
        return

    # 获取视频信息
    video = get_video_by_id(video_id)
    if not video:
        st.error("视频不存在")
        return

    # 获取博主信息
    blogger = get_blogger_by_id(video['blogger_id'])

    # 返回按钮
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ 返回主页"):
            st.session_state.update({'page': 'home', 'current_video_id': None})
            st.rerun()

    with col2:
        if st.button("📊 查看详情"):
            st.session_state['page'] = 'detail'
            st.rerun()

    st.divider()

    # 显示视频基础信息
    st.subheader(f"📹 {video['title']}")
    st.info(f"博主: {blogger['nickname']} | 发布时间: {datetime.fromisoformat(video['publish_time']).strftime('%Y-%m-%d %H:%M')}")

    # 获取已有数据
    existing_metrics = get_metrics_by_video(video_id)
    existing_time_points = {m['time_point']: m for m in existing_metrics}

    # 选择时间节点
    st.divider()
    st.write("### 选择录入时间节点")

    time_point_options = []

    # 添加必录时间节点
    for tp in REQUIRED_TIME_POINTS:
        if tp in existing_time_points:
            time_point_options.append((tp, f"{tp}小时（已录入）", True))
        else:
            time_point_options.append((tp, f"{tp}小时（必录）", False))

    # 添加可选时间节点
    for tp in OPTIONAL_TIME_POINTS:
        if tp in existing_time_points:
            time_point_options.append((tp, f"{tp}小时（已录入）", True))
        else:
            time_point_options.append((tp, f"{tp}小时（可选）", False))

    selected_tp_label = st.selectbox(
        "选择时间节点",
        options=[label for _, label, _ in time_point_options],
        index=0,
        key="time_point_selector"
    )

    # 找到选择的时间节点
    selected_tp = None
    for tp, label, has_data in time_point_options:
        if label == selected_tp_label:
            selected_tp = tp
            break

    if not selected_tp:
        st.error("请选择一个时间节点")
        return

    st.divider()
    st.write(f"### 录入 {selected_tp}h 流量数据")

    # 如果已有数据，预填充
    existing_data = existing_time_points.get(selected_tp, {})

    # 数据录入表单
    with st.form(f"metrics_form_{selected_tp}"):
        st.write("#### 核心指标")

        # 播放量
        play_count_default = existing_data.get('play_count', 0) if existing_data else 0
        play_count = st.number_input(
            "播放量 *",
            min_value=0,
            value=play_count_default,
            step=1,
            help="与小红书后台数据一致"
        )

        # 点赞数
        like_count_default = existing_data.get('like_count', 0) if existing_data else 0
        like_count = st.number_input(
            "点赞数 *",
            min_value=0,
            value=like_count_default,
            step=1
        )

        # 收藏数
        collect_count_default = existing_data.get('collect_count', 0) if existing_data else 0
        collect_count = st.number_input(
            "收藏数 *",
            min_value=0,
            value=collect_count_default,
            step=1
        )

        # 评论数
        comment_count_default = existing_data.get('comment_count', 0) if existing_data else 0
        comment_count = st.number_input(
            "评论数 *",
            min_value=0,
            value=comment_count_default,
            step=1
        )

        # 完播率
        completion_rate_default = existing_data.get('completion_rate', 0.0) if existing_data else 0.0
        completion_rate = st.number_input(
            "完播率(%) *",
            min_value=0.0,
            max_value=100.0,
            value=completion_rate_default,
            step=0.1,
            help="与小红书后台数据一致，百分比"
        )

        col_submit, col_clear = st.columns(2)

        with col_submit:
            submit = st.form_submit_button("保存数据", type="primary", use_container_width=True)

        with col_clear:
            if st.form_submit_button("清空表单", use_container_width=True)

        if submit:
            # 数据验证
            valid, error, data = validate_metrics_data(
                str(play_count),
                str(like_count),
                str(collect_count),
                str(comment_count),
                str(completion_rate)
            )

            if not valid:
                st.error(error)
            else:
                # 保存数据
                upsert_metrics(
                    video_id=video_id,
                    time_point=selected_tp,
                    play_count=data['play_count'],
                    like_count=data['like_count'],
                    collect_count=data['collect_count'],
                    comment_count=data['comment_count'],
                    completion_rate=data['completion_rate']
                )

                st.success(f"成功保存 {selected_tp}h 流量数据！")

                # 显示必录数据完成情况
                st.divider()
                st.write("### 📋 必录数据完成情况")

                required_data = []
                for tp in REQUIRED_TIME_POINTS:
                    m = get_metrics_by_video_and_time_point(video_id, tp)
                    status = "✅ 已录入" if m else "❌ 未录入"
                    required_data.append({
                        '时间节点': f"{tp}h",
                        '状态': status
                    })

                df = pd.DataFrame(required_data)
                st.dataframe(df, use_container_width=True, hide_index=True)

                # 检查是否所有必录数据已完成
                all_required_done = all(
                    get_metrics_by_video_and_time_point(video_id, tp)
                    for tp in REQUIRED_TIME_POINTS
                )

                if all_required_done:
                    st.success("🎉 所有必录数据（1h/4h/8h）已完成！")
                else:
                    st.warning("请继续录入其他必录时间节点的数据")

    # 显示已有数据预览
    if existing_metrics:
        st.divider()
        st.write("### 已录入数据预览")

        data = []
        for m in existing_metrics:
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
