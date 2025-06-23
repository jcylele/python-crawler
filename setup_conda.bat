@echo off
echo 正在创建Conda环境...

REM 检查conda是否安装
conda --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到conda，请先安装Anaconda或Miniconda
    pause
    exit /b 1
)

REM 创建环境
conda env create -f environment.yml

if errorlevel 1 (
    echo 环境创建失败
    pause
    exit /b 1
)

echo 环境创建成功！
echo 激活环境: conda activate crawler
echo 运行项目: python run.py
pause