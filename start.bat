@echo off
chcp 65001 > nul
echo 激活Conda环境...
call conda activate crawler

if errorlevel 1 (
    echo 环境激活失败，请先运行 setup_conda.bat
    pause
    exit /b 1
)

echo 启动Web服务器...
python run.py
pause