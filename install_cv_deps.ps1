# 安装LOLHelper CV检测所需依赖

Write-Host "开始安装LOLHelper CV视觉检测依赖包..." -ForegroundColor Green
Write-Host ""

# CV检测核心依赖
Write-Host "[1/4] 安装OpenCV..." -ForegroundColor Cyan
pip install opencv-python --upgrade

Write-Host ""
Write-Host "[2/4] 安装NumPy..." -ForegroundColor Cyan
pip install numpy --upgrade

Write-Host ""
Write-Host "[3/4] 安装MSS屏幕截图库..." -ForegroundColor Cyan
pip install mss --upgrade

Write-Host ""
Write-Host "[4/4] 安装Ultralytics YOLO..." -ForegroundColor Cyan
pip install ultralytics --upgrade

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "✅ 所有依赖安装完成！" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

Write-Host ""
Write-Host "可选：安装GPU加速支持 (需要CUDA)" -ForegroundColor Yellow
Write-Host "如果你有NVIDIA显卡，运行以下命令可以获得更好的性能：" -ForegroundColor Yellow
Write-Host "pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118" -ForegroundColor White

Write-Host ""
Write-Host "下一步：" -ForegroundColor Cyan
Write-Host "1. 运行 python app_new.py 启动应用" -ForegroundColor White
Write-Host "2. 浏览器打开 http://localhost:5000" -ForegroundColor White
Write-Host "3. 点击 'CV视觉检测' 按钮测试功能" -ForegroundColor White

Write-Host ""
Write-Host "查看完整使用说明：CV_DETECTION_GUIDE.md" -ForegroundColor Magenta
