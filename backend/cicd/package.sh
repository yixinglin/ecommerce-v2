#!/bin/bash

# 将当前目录下的项目打包为压缩文件
echo "Packaging project..."
tar -zcvf project.tar.gz \
                --exclude="database/*"  \
                --exclude="logs/*" \
                --exclude="venv/*" \
                --exclude="*.pyc" \
                --exclude="*.png" \
                --exclude="*.jpg" \
                --exclude="*.jpeg" \
                --exclude="build/*" \
                --exclude="__pycache__" \
                --exclude="static2/*"  \
                --exclude="scripts/*" \
                ./*

                 
# 将打包好的文件移动到build目录下
if [ ! -d "./build" ]; then
    mkdir build
fi

mv project.tar.gz ./build
echo "Packaged project successfully."