#!/bin/bash
# 启动脚本

echo "========================================"
echo "股票/基金数据监控面板"
echo "========================================"
echo ""

# 创建data目录
mkdir -p data

# 启动服务
echo "正在启动服务..."
echo "访问地址："
echo "  前端: http://localhost:8000/"
echo "  API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

cd "$(dirname "$0")"
exec python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
