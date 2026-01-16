@echo off
set "SOURCE=dist\web"
set "DEST=D:\OnlyFans\__app"

echo Deploying from %SOURCE% to %DEST%...

REM 复制 exe
copy /Y "%SOURCE%\web.exe" "%DEST%\"
echo Copied web.exe

REM 复制依赖文件夹 _internal
REM /MIR: 镜像（复制所有，删除多余）
REM /NFL /NDL: 不列出具体文件名和目录名（减少刷屏）
REM /NP: 不显示进度百分比
robocopy "%SOURCE%\_internal" "%DEST%\_internal" /MIR /NFL /NDL /NP

echo Done.
pause