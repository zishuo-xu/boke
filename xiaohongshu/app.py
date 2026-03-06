"""
小红书博主视频早期流量追踪工具

专为小红书博主设计的轻量化视频早期流量监控工具，
支持记录并可视化展示视频发布后1h、4h、8h、24h的关键数据。
"""
import streamlit as st
from pages.home import render_home
from pages.entry import render_entry
from pages.detail import render_detail


def main():
    """主应用入口"""
    # 配置页面
    st.set_page_config(
        page_title="小红书博主视频早期流量追踪工具",
        page_icon="📱",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 自定义CSS样式
    st.markdown("""
        <style>
        .stApp {
            max-width: 1400px;
        }
        .stButton > button {
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)

    # 获取当前页面
    current_page = st.session_state.get('page', 'home')

    # 根据页面路由渲染不同内容
    if current_page == 'home':
        render_home()
    elif current_page == 'entry':
        render_entry()
    elif current_page == 'detail':
        render_detail()
    else:
        st.session_state['page'] = 'home'
        render_home()


if __name__ == "__main__":
    main()
