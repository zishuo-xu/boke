#!/bin/bash
# RAG Visualization 部署脚本
# 用法:
#   SERVER_IP=1.2.3.4 SERVER_USER=root SERVER_PASS=xxx ./deploy.sh

set -e

# 服务器信息
SERVER_IP="${SERVER_IP:-}"
SERVER_USER="${SERVER_USER:-root}"
SERVER_PASS="${SERVER_PASS:-}"
PROJECT_DIR="${PROJECT_DIR:-/root/rag_share}"

if [ -z "$SERVER_IP" ] || [ -z "$SERVER_PASS" ]; then
    echo "请先提供 SERVER_IP 和 SERVER_PASS 环境变量"
    exit 1
fi

echo "=== 1. 上传代码到服务器 ==="
export SSHPASS="$SERVER_PASS"
sshpass -o StrictHostKeyChecking=no scp -r . ${SERVER_USER}@${SERVER_IP}:${PROJECT_DIR}

echo "=== 2. 在服务器上安装 Docker（如需要） ==="
sshpass ssh -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
if ! command -v docker &> /dev/null; then
    echo "安装 Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

# 创建 .env 文件（如果不存在）
if [ ! -f ${PROJECT_DIR}/.env ]; then
    cp ${PROJECT_DIR}/.env.example ${PROJECT_DIR}/.env
    echo "请编辑 ${PROJECT_DIR}/.env 填写 API Keys"
fi

echo "=== 3. 构建并启动服务 ==="
cd ${PROJECT_DIR}
docker compose up -d --build

echo "=== 4. 检查服务状态 ==="
docker compose ps

echo ""
echo "=== 部署完成 ==="
echo "前端地址: http://${SERVER_IP}"
echo "容器状态请执行: docker compose ps"
echo ""
echo "请在阿里云控制台开放 80 端口的安全组规则"
ENDSSH
