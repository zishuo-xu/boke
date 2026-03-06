"""主页：博主选择+视频列表"""
import streamlit as st
from datetime import datetime
from models.blogger import get_all_bloggers, get_blogger_by_id
from models.video import get_videos_by_blogger
from components.blogger_selector import render_blogger_management
from components.video_list import render_video_filters, render_add_video_dialog, render_video_list
from components.export_dialog import render_export_dialog


def render_home():
    """渲染主页"""
    st.title("📱 小红书博主视频早期流量追踪工具")

    # 初始化session状态
    if 'current_blogger_id' not in st.session_state:
        st.session_state['current_blogger_id'] = None
    if 'page' not in st.session_state:
        st.session_state['page'] = 'home'

    # 侧边栏：博主管理
    with st.sidebar:
        st.header("👤 博主管理")
        render_blogger_management()

    # 主内容区
    bloggers = get_all_bloggers()

    if not bloggers:
        st.info("欢迎使用小红书博主视频早期流量追踪工具！请先在左侧添加博主。")
        return

    # 获取当前博主
    current_blogger_id = st.session_state.get('current_blogger_id')
    if current_blogger_id is None:
        current_blogger_id = bloggers[0]['id']
        st.session_state['current_blogger_id'] = current_blogger_id

    current_blogger = get_blogger_by_id(current_blogger_id)

    # 顶部博主选择器
    st.divider()
    col1, col2 = st.columns([3, 1])

    with col1:
        options = {b['id']: b['nickname'] for b in bloggers}
        selected_id = st.selectbox(
            "当前博主",
            options=list(options.keys()),
            format_func=lambda x: options[x],
            index=list(options.keys()).index(current_blogger_id),
            key="home_blogger_selector"
        )
        if selected_id != current_blogger_id:
            st.session_state['current_blogger_id'] = selected_id
            st.rerun()

    with col2:
        if st.button("刷新", use_container_width=True):
            st.rerun()

    st.divider()

    # 获取该博主的所有视频
    videos = get_videos_by_blogger(current_blogger_id)

    # 标签页
    tab1, tab2, tab3 = st.tabs(["📹 视频列表", "➕ 新增视频", "📤 导出数据"])

    with tab1:
        st.subheader(f"{current_blogger['nickname']} 的视频")

        # 筛选条件
        filtered_videos = render_video_filters(current_blogger_id)

        if filtered_videos:
            render_video_list(current_blogger_id, filtered_videos)
        else:
            st.info("没有找到符合筛选条件的视频")

    with tab2:
        render_add_video_dialog(current_blogger_id)

    with tab3:
        render_export_dialog(current_blogger_id, current_blogger['nickname'], videos)
