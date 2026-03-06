"""视频列表组件"""
import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime
from models.video import get_videos_by_blogger, search_videos, filter_videos_by_date, filter_videos_by_performance
from models.metrics import get_metrics_by_video


def render_video_list(blogger_id: int, videos: List[Dict[str, Any]]):
    """渲染视频列表

    Args:
        blogger_id: 博主ID
        videos: 视频列表
    """
    if not videos:
        st.info("暂无视频，请先添加视频")
        return

    # 为每个视频添加流量数据
    metrics_data = {}
    for video in videos:
        metrics_data[video['id']] = get_metrics_by_video(video['id'])

    # 显示视频列表
    for video in videos:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([4, 2, 2, 2])

            with col1:
                st.write(f"**{video['title']}**")

            with col2:
                pub_time = datetime.fromisoformat(video['publish_time'])
                st.write(f"{pub_time.strftime('%Y-%m-%d %H:%M')}")

            # 显示1h和8h播放量
            metrics = metrics_data.get(video['id'], {})
            with col3:
                h1_play = next((m['play_count'] for m in metrics if m['time_point'] == 1), '-')
                st.write(f"1h播放: {h1_play}")

            with col4:
                h8_play = next((m['play_count'] for m in metrics if m['time_point'] == 8), '-')
                st.write(f"8h播放: {h8_play}")

            # 操作按钮
            col_btn1, col_btn2, col_btn3 = st.columns(3)

            with col_btn1:
                if st.button("查看详情", key=f"detail_{video['id']}", use_container_width=True):
                    st.session_state['current_video_id'] = video['id']
                    st.session_state['page'] = 'detail'
                    st.rerun()

            with col_btn2:
                if st.button("录入数据", key=f"entry_{video['id']}", use_container_width=True):
                    st.session_state['current_video_id'] = video['id']
                    st.session_state['page'] = 'entry'
                    st.rerun()

            with col_btn3:
                if st.button("编辑", key=f"edit_video_{video['id']}", use_container_width=True):
                    st.session_state[f'editing_video_{video["id"]}'] = True

            # 编辑模态框
            if st.session_state.get(f'editing_video_{video["id"]}', False):
                with st.expander(f"编辑视频 - {video['title']}", expanded=True):
                    with st.form(f"edit_video_{video['id']}"):
                        new_title = st.text_input("视频标题", value=video['title'], max_chars=50)
                        new_link = st.text_input("视频链接", value=video['video_link'])
                        pub_time = datetime.fromisoformat(video['publish_time'])
                        new_pub_time = st.datetime_input("发布时间", value=pub_time)
                        new_tags = st.text_area("标签（可选）", value=video['tags'] or '')

                        col_cancel, col_submit = st.columns(2)

                        with col_cancel:
                            if st.form_submit_button("取消"):
                                st.session_state[f'editing_video_{video["id"]}'] = False
                                st.rerun()

                        with col_submit:
                            if st.form_submit_button("保存"):
                                from models.video import update_video
                                from utils.validators import validate_video_title, validate_video_link

                                valid, error = validate_video_title(new_title)
                                if not valid:
                                    st.error(error)
                                else:
                                    valid, error = validate_video_link(new_link)
                                    if not valid:
                                        st.error(error)
                                    else:
                                        update_video(
                                            video['id'],
                                            title=new_title,
                                            video_link=new_link,
                                            publish_time=new_pub_time,
                                            tags=new_tags if new_tags else None
                                        )
                                        st.success("更新成功")
                                        st.session_state[f'editing_video_{video["id"]}'] = False
                                        st.rerun()


def render_video_filters(blogger_id: int) -> List[Dict[str, Any]]:
    """渲染视频筛选器

    Args:
        blogger_id: 博主ID

    Returns:
        筛选后的视频列表
    """
    # 获取筛选方式
    filter_method = st.radio(
        "筛选方式",
        ["全部", "按时间", "按流量表现", "搜索"],
        horizontal=True
    )

    videos = []

    if filter_method == "全部":
        videos = get_videos_by_blogger(blogger_id)

    elif filter_method == "按时间":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("开始日期")
        with col2:
            end_date = st.date_input("结束日期")

        if start_date and end_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            videos = filter_videos_by_date(blogger_id, start_datetime, end_datetime)

    elif filter_method == "按流量表现":
        col1, col2 = st.columns(2)
        with col1:
            filter_type = st.selectbox("流量类型", ["全部", "爆款", "低流量"])
        with col2:
            st.write("筛选阈值")
            high_threshold = st.number_input("爆款阈值（播放量）", value=10000, min_value=0)
            low_threshold = st.number_input("低流量阈值（播放量）", value=1000, min_value=0)

        type_map = {"全部": "all", "爆款": "high", "低流量": "low"}
        videos = filter_videos_by_performance(
            blogger_id,
            type_map[filter_type],
            high_threshold,
            low_threshold
        )

    elif filter_method == "搜索":
        keyword = st.text_input("搜索关键词（标题/链接）")
        if keyword:
            videos = search_videos(blogger_id, keyword)
        else:
            videos = get_videos_by_blogger(blogger_id)

    return videos


def render_add_video_dialog(blogger_id: int):
    """渲染添加视频对话框

    Args:
        blogger_id: 博主ID
    """
    with st.expander("新增视频", expanded=True):
        with st.form("add_video"):
            title = st.text_input("视频标题 *", max_chars=50)
            video_link = st.text_input("视频链接 *")
            publish_time = st.datetime_input("发布时间 *")
            tags = st.text_area("标签（可选，用逗号分隔）")

            submit = st.form_submit_button("添加视频")

            if submit:
                from models.video import add_video
                from utils.validators import validate_video_title, validate_video_link

                valid, error = validate_video_title(title)
                if not valid:
                    st.error(error)
                else:
                    valid, error = validate_video_link(video_link)
                    if not valid:
                        st.error(error)
                    else:
                        video_id = add_video(
                            blogger_id=blogger_id,
                            title=title,
                            video_link=video_link,
                            publish_time=publish_time,
                            tags=tags if tags else None
                        )
                        st.success(f"成功添加视频：{title}")
                        st.rerun()
