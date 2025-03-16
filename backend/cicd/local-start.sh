#!/bin/bash

VENV_DIR="venv"
PYINTERPRETER="python3.12"
APP_ENV="dev"

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

if [ ! -x "$(command -v $PYINTERPRETER)" ]; then
    echo "Python interpreter $PYINTERPRETER not found"
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment $VENV_DIR"
    $PYINTERPRETER -m venv $VENV_DIR
fi

echo "Activating virtual environment $VENV_DIR"
source $VENV_DIR/bin/activate

echo "Installing requirements"
python3 -m pip install --upgrade pip
pip install -r requirements.txt

echo "Starting server"
export ENV=$APP_ENV
python main.py

echo "Deactivating virtual environment $VENV_DIR"
deactivate
