# 常量定义

# 数据库文件名
DATABASE_FILE = "xiaohongshu.db"

# 时间节点（小时）
TIME_POINTS = [1, 4, 8, 24]

# 必录时间节点
REQUIRED_TIME_POINTS = [1, 4, 8]

# 可选时间节点
OPTIONAL_TIME_POINTS = [24]

# 流量指标
METRICS = {
    "play_count": "播放量",
    "like_count": "点赞数",
    "collect_count": "收藏数",
    "comment_count": "评论数",
    "completion_rate": "完播率(%)"
}

# 流量分类阈值（默认值）
DEFAULT_THRESHOLD_HIGH = 10000   # 播放量大于此值视为爆款
DEFAULT_THRESHOLD_LOW = 1000     # 播放量小于此值视为低流量
