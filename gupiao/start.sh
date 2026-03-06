#!/bin/bash
# 快速启动脚本

echo "========================================"
echo "股票/基金数据监控面板 - 启动脚本"
echo "========================================"
echo ""

# 检查Python版本
PYTHON_VERSION=$(python3 --version 2>&1 | head -n 1)
echo "Python版本: $PYTHON_VERSION"
echo ""

# 安装依赖
echo "正在安装Python依赖..."
python3 -m pip install --break-system-packages --quiet -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ 依赖安装成功！"
else
    echo "✗ 依赖安装失败"
    echo ""
    echo "尝试手动安装："
    echo "  cd /Users/xuzishuo/ai-work/gupiao"
    echo "  python3 -m pip install --break-system-packages -r requirements.txt"
    exit 1
fi

# 创建data目录
echo "创建data目录..."
mkdir -p data

# 启动服务
echo ""
echo "========================================"
echo "正在启动服务..."
echo "========================================"
echo ""
echo "访问地址:"
echo "  前端: http://localhost:8000/"
echo "  API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
