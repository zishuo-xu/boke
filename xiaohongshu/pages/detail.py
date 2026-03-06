"""视频详情页"""
import streamlit as st
from models.blogger import get_blogger_by_id
from models.video import get_video_by_id
from components.data_card import render_data_card, render_metrics_chart


def render_detail():
    """渲染视频详情页"""
    st.title("📊 视频详情")

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
        st.button("返回主页", on_click=lambda: st.session_state.update({'page': 'home', 'current_video_id': None}))
        return

    # 获取博主信息
    blogger = get_blogger_by_id(video['blogger_id'])

    # 顶部操作按钮
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("⬅️ 返回主页"):
            st.session_state.update({'page': 'home', 'current_video_id': None})
            st.rerun()

    with col2:
        if st.button("📝 录入数据"):
            st.session_state['page'] = 'entry'
            st.rerun()

    with col3:
        if st.button("🔄 刷新"):
            st.rerun()

    st.divider()

    # 渲染数据卡片
    render_data_card(video, blogger)

    st.divider()

    # 渲染流量曲线图
    render_metrics_chart(video)

    # 快速数据录入入口
    st.divider()
    st.write("### 快速操作")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📝 录入数据", use_container_width=True):
            st.session_state['page'] = 'entry'
            st.rerun()

    with col2:
        if st.button("📋 复制视频链接", use_container_width=True):
            st.session_state['copied_link'] = video['video_link']
            st.toast("链接已复制到剪贴板")

    with col3:
        if st.button("🔙 返回列表", use_container_width=True):
            st.session_state.update({'page': 'home', 'current_video_id': None})
            st.rerun()
