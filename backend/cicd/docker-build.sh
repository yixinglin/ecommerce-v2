#!/bin/bash

# 复制配置文件conf
if [ ! -d "conf" ]; then
    echo "conf directory not found"
    exit 1
fi

# Ask if user wants to update
read -p "Do you want to update the code? (y/n) " answer
if [ "$answer" == "y" ]; then
    echo "Updating code from git"
    cd ../
    git pull  
    cd ./backend
fi

docker compose down
docker compose up --build -d

# 等待容器启动
echo "Waiting for containers to start..."
sleep 5  # 这里等待 5 秒，你可以调整时间

# 获取 docker compose 相关容器的状态
CONTAINER_STATUS=$(docker compose ps --format "{{.Name}}: {{.State}}" | grep -v "Exit")

# 检查是否所有容器都在运行
if echo "$CONTAINER_STATUS" | grep -q "running"; then
    echo "✅ All containers started successfully!"
else
    echo "❌ Some containers failed to start!"
    echo "⏳ Current container status:"
    docker compose ps
    exit 1  # 返回错误码，表示启动失败
fi

echo "Done!"
