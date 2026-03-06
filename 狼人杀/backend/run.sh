#!/bin/bash

# AI机器人狼人杀 - 启动脚本


echo "===================================="
echo "  AI机器人狼人杀"
echo "===================================="

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到Python3，请先安装Python3"
    exit 1
fi

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装依赖包..."
pip install -r requirements.txt -q

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "创建配置文件..."
    cp .env.example .env
    echo "请编辑.env文件配置LLM API密钥（可选）"
fi

# 启动服务器
echo ""
echo "启动服务器..."
echo "访问地址: http://localhost:5000"
echo "按 Ctrl+C 停止服务器"
echo ""

python app.py
