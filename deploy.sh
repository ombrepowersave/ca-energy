#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== 项目自动化部署脚本启动 ===${NC}"

# 检查 docker 命令是否存在
if ! command -v docker &> /dev/null
then
    echo -e "${YELLOW}未检测到 Docker，正在开始安装...${NC}"
    
    apt-get update
    
    apt-get install -y ca-certificates curl gnupg
    
    # 添加 Docker 的官方 GPG 密钥
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    # 设置 Docker 的 apt 仓库
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    apt-get update
    
    # 安装 Docker Engine, CLI, Containerd, 和 Docker Compose 插件
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    echo -e "${GREEN}Docker 安装完成！${NC}"
else
    echo -e "${GREEN}Docker 已安装，跳过安装步骤。${NC}"
fi

if ! docker compose version &> /dev/null
then
    echo -e "${RED}Docker Compose V2 (docker compose) 未找到!${NC}"
    echo -e "${YELLOW}请确保您的 Docker 版本支持 'compose' 插件 (通常随 Docker Desktop 或新版 Linux 安装包提供)。${NC}"
    echo -e "${YELLOW}尝试检查 docker-compose-plugin 是否已正确安装。${NC}"
    exit 1
fi

# --- 步骤 2: 停止并移除旧的应用容器 ---

echo -e "${YELLOW}正在停止并移除旧的 'caiso_web' 容器 (如果存在)...${NC}"
# 'docker compose down' 会停止并移除 docker-compose.yml 中定义的服务
# '|| true' 确保在服务不存在时脚本也不会因失败而退出
docker compose down || true

# --- 步骤 3: 构建新的 Docker 镜像 ---

echo -e "${YELLOW}正在构建新的 Docker 镜像 (caiso-web)...${NC}"
# 'docker compose build' 会根据 Dockerfile 重新构建镜像
docker compose build

# --- 步骤 4: 启动新的 Docker 容器 ---

echo -e "${YELLOW}正在后台启动新的容器...${NC}"
# '-d' (detached) 表示在后台运行
docker compose up -d

# --- 步骤 5: 完成 ---

echo -e "${GREEN}=== 部署完成! ===${NC}"
echo -e "您可以使用 ${YELLOW}'docker ps'${NC} 查看正在运行的容器。"
echo -e "您可以使用 ${YELLOW}'docker compose logs -f'${NC} 查看实时日志。"