@echo off
title Writenix Tech Solutions - Disk Optimizer
cd /d "%~dp0"
if exist "dist\WritenixDiskOptimizer.exe" (
    start "" "dist\WritenixDiskOptimizer.exe"
) else (
    python writenix_optimizer.py
)
exit
