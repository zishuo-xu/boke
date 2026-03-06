"""博主选择器组件"""
import streamlit as st
from typing import Optional
from models.blogger import get_all_bloggers, get_blogger_by_id


def render_blogger_selector() -> Optional[int]:
    """渲染博主选择器

    Returns:
        选中的博主ID，如果没有选中则返回None
    """
    # 获取所有博主
    bloggers = get_all_bloggers()

    if not bloggers:
        st.warning("暂无博主，请先添加博主")
        return None

    # 构建选项
    options = {b['id']: b['nickname'] for b in bloggers}
    options['all'] = '全部博主'

    # 获取当前选中的博主
    current_blogger_id = st.session_state.get('current_blogger_id', None)

    # 默认选择第一个博主
    if current_blogger_id is None and bloggers:
        current_blogger_id = bloggers[0]['id']
        st.session_state['current_blogger_id'] = current_blogger_id

    # 渲染选择器
    # 找到当前博主对象
    current_blogger_obj = next((b for b in bloggers if b['id'] == current_blogger_id), None)

    selected = st.selectbox(
        "选择博主",
        options=[None] + list(bloggers),
        format_func=lambda x: '全部博主' if x is None else x['nickname'],
        index=list(bloggers).index(current_blogger_obj) + 1 if current_blogger_obj else 0,
        key="blogger_selector"
    )

    if selected:
        st.session_state['current_blogger_id'] = selected['id']
        return selected['id']

    return None


def render_blogger_management():
    """渲染博主管理界面"""
    st.subheader("博主管理")

    # 新增博主
    with st.expander("新增博主"):
        with st.form("add_blogger"):
            nickname = st.text_input("博主昵称 *", max_chars=20)
            account_link = st.text_input("小红书账号链接（可选）")
            note = st.text_area("备注（可选）")

            submit = st.form_submit_button("添加")

            if submit:
                from models.blogger import add_blogger
                from utils.validators import validate_nickname

                valid, error = validate_nickname(nickname)
                if not valid:
                    st.error(error)
                else:
                    blogger_id = add_blogger(
                        nickname=nickname,
                        account_link=account_link if account_link else None,
                        note=note if note else None
                    )
                    st.success(f"成功添加博主：{nickname}")
                    st.rerun()

    # 博主列表
    bloggers = get_all_bloggers()
    if bloggers:
        st.divider()
        st.write("### 博主列表")

        for blogger in bloggers:
            col1, col2, col3, col4 = st.columns([3, 4, 2, 2])

            with col1:
                st.write(f"**{blogger['nickname']}**")

            with col2:
                if blogger['account_link']:
                    st.markdown(f"[账号链接]({blogger['account_link']})")

            with col3:
                video_count = blogger.get('video_count', 0)
                st.write(f"{video_count}个视频")

            with col4:
                edit_btn = st.button("编辑", key=f"edit_blogger_{blogger['id']}")
                delete_btn = st.button("删除", key=f"delete_blogger_{blogger['id']}", type="secondary")

                if edit_btn:
                    st.session_state[f'editing_blogger_{blogger["id"]}'] = True

                if delete_btn:
                    st.session_state[f'deleting_blogger_{blogger["id"]}'] = True

            # 编辑模态框
            if st.session_state.get(f'editing_blogger_{blogger["id"]}', False):
                with st.expander(f"编辑博主 - {blogger['nickname']}", expanded=True):
                    with st.form(f"edit_blogger_{blogger['id']}"):
                        new_nickname = st.text_input("博主昵称", value=blogger['nickname'], max_chars=20)
                        new_account_link = st.text_input("小红书账号链接", value=blogger['account_link'] or '')
                        new_note = st.text_area("备注", value=blogger['note'] or '')

                        col_cancel, col_submit = st.columns(2)

                        with col_cancel:
                            if st.form_submit_button("取消"):
                                st.session_state[f'editing_blogger_{blogger["id"]}'] = False
                                st.rerun()

                        with col_submit:
                            if st.form_submit_button("保存"):
                                from models.blogger import update_blogger
                                from utils.validators import validate_nickname

                                valid, error = validate_nickname(new_nickname)
                                if not valid:
                                    st.error(error)
                                else:
                                    update_blogger(
                                        blogger['id'],
                                        nickname=new_nickname,
                                        account_link=new_account_link if new_account_link else None,
                                        note=new_note if new_note else None
                                    )
                                    st.success("更新成功")
                                    st.session_state[f'editing_blogger_{blogger["id"]}'] = False
                                    st.rerun()

            # 删除确认
            if st.session_state.get(f'deleting_blogger_{blogger["id"]}', False):
                st.warning(f"确定要删除博主「{blogger['nickname']}」吗？删除后将同时删除该博主的所有视频和数据！")
                col_confirm, col_cancel = st.columns(2)

                with col_confirm:
                    if st.button("确认删除", key=f"confirm_delete_{blogger['id']}", type="primary"):
                        from models.blogger import delete_blogger
                        delete_blogger(blogger['id'])
                        st.success("删除成功")

                        # 清理session状态
                        if st.session_state.get('current_blogger_id') == blogger['id']:
                            st.session_state['current_blogger_id'] = None

                        del st.session_state[f'deleting_blogger_{blogger["id"]}']
                        st.rerun()

                with col_cancel:
                    if st.button("取消", key=f"cancel_delete_{blogger['id']}"):
                        del st.session_state[f'deleting_blogger_{blogger["id"]}']
                        st.rerun()

            st.divider()
