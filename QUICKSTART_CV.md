# 🚀 LOLHelper CV检测 - 快速启动指南

## 📦 安装依赖（首次运行必须）

打开PowerShell，在项目目录运行：

```powershell
.\install_cv_deps.ps1
```

这会自动安装：
- opencv-python（图像处理）
- numpy（数组计算）
- mss（屏幕截图）
- ultralytics（YOLO模型）

**预计安装时间：** 2-5分钟（取决于网速）

---

## ✅ 验证安装

运行测试脚本确认所有模块正常：

```bash
python test_cv_detection.py
```

**预期结果：**
```
🎉 所有测试通过！CV检测功能准备就绪
总计: 6/6 测试通过
```

---

## 🎮 启动应用

```bash
python app_new.py
```

**看到以下信息表示启动成功：**
```
* Running on http://127.0.0.1:5000
```

---

## 🌐 访问CV检测功能

### 方式1：从主页进入
1. 浏览器打开：http://localhost:5000
2. 点击黄色按钮："CV视觉检测"

### 方式2：直接访问
浏览器打开：http://localhost:5000/vision_detection

---

## 🎯 使用CV检测

### 步骤1：开始检测
1. 确保游戏正在运行（或有游戏画面）
2. 点击页面左上角的**绿色"开始检测"**按钮
3. 等待1-2秒，YOLO模型加载完成

### 步骤2：查看检测结果
- **左侧面板**：显示实时统计数据
  - 抬手检测次数
  - 敌人发现次数
  
- **右侧4个面板**：分类显示检测结果
  - 英雄抬手
  - 小地图敌人
  - 危险信号
  - 技能指示器

### 步骤3：接收警报
- 检测到重要事件时会弹出警报通知
- 警报自动5秒后消失
- 警报等级：
  - 🟢 低 - 一般信息
  - 🟡 中 - 需要注意
  - 🔴 高 - 重要警报

### 步骤4：手动截图（可选）
1. 点击**蓝色"手动截图"**按钮
2. 截图保存在 `detections/` 目录
3. 文件名格式：`detection_YYYYMMDD_HHMMSS.png`
4. 截图会自动标注所有检测框

### 步骤5：停止检测
- 点击**红色"停止检测"**按钮
- 或直接关闭浏览器标签页

---

## ⚙️ 调整设置（高级）

### 修改检测频率

编辑 `services/vision_service.py`，找到：

```python
vision_detection_task(socketio, detection_interval=1.0)
```

将 `1.0` 改为其他值：
- `0.5` = 每0.5秒检测一次（更快但消耗更多资源）
- `2.0` = 每2秒检测一次（更慢但省资源）

### 修改检测区域

编辑 `services/game_vision.py`，找到 `self.regions`：

```python
self.regions = {
    'minimap': {
        'x': 0,      # 小地图左边缘（0-1比例）
        'y': 0.75,   # 小地图上边缘
        'width': 0.15,   # 宽度
        'height': 0.25   # 高度
    },
    # ... 其他区域
}
```

### 修改置信度阈值

在检测函数中调整 `confidence_threshold`：

```python
results = detector.detect_objects(img, confidence_threshold=0.5)
```

- 降低值（如0.3）= 更多检测但可能误报
- 提高值（如0.7）= 更少检测但更准确

---

## ❓ 常见问题

### Q1: 安装ultralytics失败
```bash
# 使用国内镜像
pip install ultralytics -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q2: 首次运行下载模型很慢
- YOLO会自动下载yolov8n.pt（约6MB）
- 需要稳定的网络连接
- 下载完成后会缓存，以后不再下载

### Q3: 检测结果不准确
- 预训练模型未针对LOL优化
- 建议训练自定义模型（参考 CV_DETECTION_GUIDE.md）
- 或调整置信度阈值

### Q4: 游戏画面全屏时无法截图
- 将游戏设置为"无边框窗口化"模式
- 推荐分辨率：1920x1080 或 2560x1440

### Q5: 检测时游戏卡顿
- 增加检测间隔（改为2秒）
- 关闭其他占用资源的程序
- 考虑使用GPU加速（需要CUDA）

### Q6: GPU加速如何开启？
```bash
# 安装CUDA版本的PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

YOLO会自动检测并使用GPU。

---

## 📊 性能参考

**最低配置：**
- CPU: Intel i5 / AMD Ryzen 5
- 内存: 8GB
- 检测间隔: 2秒

**推荐配置：**
- CPU: Intel i7 / AMD Ryzen 7
- 内存: 16GB
- 显卡: GTX 1660 或更好（GPU加速）
- 检测间隔: 1秒

**预期性能：**
- CPU检测速度: 0.3-0.8秒/帧
- GPU检测速度: 0.05-0.2秒/帧
- 内存占用: ~500MB

---

## 📚 进阶学习

- **完整文档**: `CV_DETECTION_GUIDE.md`
- **模型训练**: 参考文档中"YOLO模型训练指南"章节
- **更新日志**: `UPDATE_LOG.md`

---

## 🆘 获取帮助

遇到问题？提供以下信息：
1. 错误截图或错误日志
2. Python版本：`python --version`
3. 显卡信息（如使用GPU）
4. 屏幕分辨率
5. 游戏设置（窗口/全屏）

---

**版本**: v2.1.0  
**最后更新**: 2025-10-02

🎉 **祝您使用愉快！**
