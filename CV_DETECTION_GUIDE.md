# 🎥 CV视觉检测功能说明

## 📋 功能概述

LOLHelper现已集成基于YOLO的计算机视觉检测功能，可以实时分析游戏画面，识别以下内容：

### 🔍 检测功能

1. **英雄抬手/施法检测** 🏹
   - 实时检测英雄的施法动作
   - 提前预警敌方技能释放
   - 帮助玩家做出更快反应

2. **小地图敌人检测** 🗺️
   - 监控小地图区域
   - 自动识别敌方英雄位置
   - 发现敌人时立即警报

3. **危险信号检测** ⚠️
   - 检测低血量状态
   - 识别危险信号标记
   - 综合评估危险等级

4. **技能指示器检测** ⚡
   - 识别技能指示器
   - 检测技能施放方向
   - 辅助躲避技能

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装基础CV库
pip install opencv-python numpy mss

# 安装YOLO
pip install ultralytics

# 可选：GPU加速（需要CUDA）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### 2. 准备YOLO模型

#### 方式A：使用预训练模型（快速测试）
```python
# 系统会自动下载YOLOv8n预训练模型
# 首次运行时需要联网下载
```

#### 方式B：训练自定义模型（推荐）
```bash
# 1. 准备数据集（需要标注游戏画面）
# 2. 使用Roboflow或LabelImg标注工具
# 3. 训练模型
python train_yolo.py

# 4. 将训练好的模型放到 models/lol_yolo.pt
```

### 3. 启动应用

```bash
python app_new.py
```

### 4. 访问CV检测页面

浏览器打开: `http://localhost:5000/vision_detection`

## 📊 界面说明

### 左侧控制面板

- **开始检测按钮** 🟢: 启动CV实时检测
- **停止检测按钮** 🔴: 停止检测服务
- **手动截图按钮** 📸: 保存当前画面并标注检测结果
- **检测状态**: 显示当前检测运行状态
- **实时统计**: 显示抬手和敌人检测次数

### 右侧可视化区域

- **英雄抬手**: 实时显示施法检测结果
- **小地图敌人**: 显示发现的敌人数量
- **危险信号**: 综合危险等级评估
- **技能指示器**: 技能施放检测
- **检测日志**: 详细的检测记录

## 🎯 使用场景

### 场景1：对线期预警
```
问题：对手突然释放技能，反应不及
解决：CV检测提前0.2-0.5秒识别抬手动作，提示躲避
```

### 场景2：小地图监控
```
问题：注意力在对线，忽略小地图敌人
解决：自动监控小地图，发现敌人立即警报
```

### 场景3：团战辅助
```
问题：团战混乱，难以识别敌方技能
解决：高亮显示技能指示器，辅助走位
```

## ⚙️ 配置说明

### 检测区域配置

在 `services/game_vision.py` 中调整：

```python
self.regions = {
    'minimap': {'x': 0, 'y': 0.75, 'width': 0.15, 'height': 0.25},
    'skills': {'x': 0.35, 'y': 0.85, 'width': 0.3, 'height': 0.15},
    'champion': {'x': 0.3, 'y': 0.3, 'width': 0.4, 'height': 0.4}
}
```

### 检测频率

在 `services/vision_service.py` 中调整：

```python
# detection_interval: 检测间隔（秒）
vision_detection_task(socketio, detection_interval=1.0)
```

### 置信度阈值

```python
# 在检测函数中调整confidence参数
detector.detect_objects(img, confidence_threshold=0.5)
```

## 🔧 技术架构

### 系统架构

```
┌─────────────────────────────────────────┐
│         游戏画面 (1920x1080)             │
└──────────────┬──────────────────────────┘
               │
               ↓ mss屏幕截图
┌─────────────────────────────────────────┐
│      GameVisionDetector                  │
│  - capture_screen()                     │
│  - detect_objects()                     │
└──────────────┬──────────────────────────┘
               │
               ↓ YOLO推理
┌─────────────────────────────────────────┐
│      YOLOv8模型                          │
│  - 输入: 游戏截图                        │
│  - 输出: 检测框 + 类别 + 置信度          │
└──────────────┬──────────────────────────┘
               │
               ↓ 事件处理
┌─────────────────────────────────────────┐
│   vision_detection_task (后台线程)       │
│  - 持续检测                              │
│  - 触发警报                              │
└──────────────┬──────────────────────────┘
               │
               ↓ Socket.IO
┌─────────────────────────────────────────┐
│      前端Web页面                          │
│  - 实时显示结果                          │
│  - 可视化警报                            │
└─────────────────────────────────────────┘
```

### 检测流程

```python
1. 启动检测
   → socket.emit('start_vision_detection')
   
2. 后台任务循环
   → while app_state.vision_detection_enabled:
   
3. 截取屏幕
   → detector.capture_screen(region)
   
4. YOLO推理
   → model(image)
   
5. 结果处理
   → 分类、计数、位置
   
6. 发送到前端
   → socketio.emit('vision_detection_update', results)
   
7. 触发警报
   → socketio.emit('alert', alert_data)
```

## 🎓 YOLO模型训练指南

### 数据准备

1. **收集游戏画面**
```bash
# 使用提供的截图工具
python collect_training_data.py
```

2. **标注数据**
- 使用 [Roboflow](https://roboflow.com/)
- 或使用 [LabelImg](https://github.com/heartexlabs/labelImg)

标注类别：
- `champion_casting` (英雄抬手)
- `enemy_champion` (敌方英雄)
- `ally_champion` (友方英雄)
- `skillshot_indicator` (技能指示器)
- `danger_ping` (危险信号)
- `low_health` (低血量)

3. **数据集格式**
```
dataset/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```

### 训练脚本

创建 `train_yolo.py`:

```python
from ultralytics import YOLO

# 加载预训练模型
model = YOLO('yolov8n.pt')

# 训练
results = model.train(
    data='dataset.yaml',  # 数据配置文件
    epochs=100,
    imgsz=640,
    batch=16,
    name='lol_yolo'
)

# 验证
metrics = model.val()

# 导出
model.export(format='onnx')
```

### 数据配置文件 `dataset.yaml`

```yaml
path: ./dataset
train: images/train
val: images/val
test: images/test

nc: 8  # 类别数量
names:
  0: champion_casting
  1: enemy_champion
  2: ally_champion
  3: skillshot_indicator
  4: danger_ping
  5: objective_spawn
  6: low_health
  7: enemy_ward
```

## 📈 性能优化

### 1. GPU加速

```python
# 检查CUDA可用性
import torch
print(torch.cuda.is_available())

# YOLO自动使用GPU
model = YOLO('lol_yolo.pt')  # 自动检测GPU
```

### 2. 降低检测分辨率

```python
# 在capture_screen后resize
img_resized = cv2.resize(img, (640, 360))
```

### 3. 区域检测

```python
# 只检测关键区域而非全屏
minimap_only = detector.capture_screen(regions['minimap'])
```

### 4. 异步处理

```python
# 使用线程池
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=2)
```

## 🐛 常见问题

### Q1: 模型文件不存在
```
错误: ⚠️ 模型文件不存在: models/lol_yolo.pt
解决: 
1. 使用预训练模型（自动下载）
2. 或训练自定义模型后放到models/目录
```

### Q2: 检测性能差
```
问题: FPS太低，游戏卡顿
解决:
1. 降低检测频率 (detection_interval=2.0)
2. 使用GPU加速
3. 降低图像分辨率
4. 只检测关键区域
```

### Q3: 检测不准确
```
问题: 误检或漏检
解决:
1. 调整置信度阈值
2. 使用自定义训练模型
3. 增加训练数据
4. 调整检测区域
```

### Q4: 安装ultralytics失败
```
错误: pip install ultralytics 失败
解决:
pip install ultralytics --upgrade
# 或使用国内镜像
pip install ultralytics -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 📦 依赖清单

```txt
# CV检测核心
opencv-python>=4.8.0
numpy>=1.24.0
mss>=9.0.0
ultralytics>=8.0.0

# 深度学习（可选，用于GPU加速）
torch>=2.0.0
torchvision>=0.15.0

# 原有依赖
flask>=2.3.0
flask-socketio>=5.3.0
requests>=2.31.0
psutil>=5.9.0
chardet>=5.1.0
```

## 🎯 未来计划

- [ ] **英雄技能数据库**: 识别具体技能类型
- [ ] **伤害预测**: 基于检测结果估算伤害
- [ ] **自动走位建议**: AI辅助躲避技能
- [ ] **回放分析**: 分析录像找出失误
- [ ] **自定义警报**: 用户自定义检测规则
- [ ] **多显示器支持**: 支持多屏幕设置
- [ ] **模型市场**: 共享训练好的模型

## 📞 技术支持

如遇问题，请提供：
1. 错误日志
2. Python版本
3. CUDA版本（如使用GPU）
4. 屏幕分辨率
5. 游戏设置（窗口/全屏）

---

**版本**: v2.1.0  
**更新日期**: 2025-10-02  
**作者**: LOLHelper Team
