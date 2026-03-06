# 日常学习博客分享系统（Flask）

基于 `需求文档.md` 的可运行实现版本，覆盖博客前台浏览与后台管理核心功能。

## 快速启动

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app run.py init-db
flask --app run.py create-admin
flask --app run.py run
```

默认管理员账号：`admin`  密码：`admin123`

## 已实现能力

- 前台：首页列表分页、文章详情 Markdown 渲染、目录导航、上一篇/下一篇、搜索（标题/摘要/正文）、分类与标签筛选、侧边栏最新文章/统计/标签云
- 安全：登录鉴权、后台管理员权限隔离、密码哈希存储、Markdown 渲染后 XSS 过滤
- 后台：文章增删改（Editor.md 双栏实时预览、草稿/发布、自动摘要、分类标签关联）、自动保存草稿、版本历史与回滚、草稿筛选/回收站恢复、分类管理、标签新增/批量删除/合并、图片上传压缩与媒体库、基础数据看板
- 数据：SQLite + SQLAlchemy 模型（user/category/tag/post/post_tag）

## 说明

- 当前为 V1 实现，优先满足核心闭环，未接入 Whoosh、图片上传与批量文章删除接口。
- 当前账号模型支持“普通用户登录 + 管理员后台隔离”：普通用户可注册登录用于前台身份能力，后台管理仍仅管理员可访问。
- 生产建议：替换 `SECRET_KEY`、使用 PostgreSQL、补充单元测试与部署配置。

## 升级提示

- 新增媒体库与版本草稿数据表后，请执行一次：
  - `flask --app run.py init-db`
