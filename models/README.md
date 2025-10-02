# 🎯 YOLO模型目录

## 📁 目录说明

此目录用于存放YOLO检测模型文件。

## 🔍 当前状态

### 使用中的模型
- ✅ **yolov8n.pt** - YOLOv8预训练模型（通用目标检测）
  - 位置: 自动下载到用户目录
  - 类别数: 80个COCO数据集类别
  - 准确度: ⚠️ 对LOL游戏画面识别有限

### 推荐模型
- 📦 **lol_yolo.pt** - LOL专用YOLO模型（需要训练）
  - 位置: 放在此目录 `models/lol_yolo.pt`
  - 类别数: 8个LOL特定类别
  - 准确度: ✅ 针对LOL优化，识别准确

## 🎓 如何获得LOL专用模型

### 方式1：训练自定义模型（推荐）

#### 步骤1：收集训练数据
```bash
# 运行数据收集脚本
python tools/collect_training_data.py

# 在游戏中按 F12 截图
# 保存到 training_data/images/
```

#### 步骤2：标注数据
使用在线工具标注：
- **Roboflow**: https://roboflow.com/ （推荐，自动导出YOLO格式）
- **LabelImg**: https://github.com/heartexlabs/labelImg

标注类别（8种）：
1. `champion_casting` - 英雄抬手/施法动作
2. `enemy_champion` - 敌方英雄
3. `ally_champion` - 友方英雄
4. `skillshot_indicator` - 技能指示器（地面标记）
5. `danger_ping` - 危险信号标记
6. `objective_spawn` - 野怪/目标刷新
7. `low_health` - 低血量指示
8. `enemy_ward` - 敌方眼位

#### 步骤3：训练模型
```bash
# 运行训练脚本
python tools/train_yolo_model.py

# 训练完成后模型会自动保存到此目录
```

### 方式2：使用预训练模型（快速测试）

当前系统会自动使用YOLOv8预训练模型，但识别准确度有限：

**预训练模型的局限性：**
- ❌ 无法识别英雄抬手动作
- ❌ 无法识别技能指示器
- ❌ 可能误识别游戏UI元素
- ⚠️ 仅适合功能测试，不适合实战

**建议：**
收集100-200张游戏截图进行标注和训练，可大幅提升准确度。

## 📊 模型性能对比

| 模型 | 准确度 | 速度 | 适用场景 |
|-----|-------|------|---------|
| yolov8n.pt | ⭐⭐ | 🚀🚀🚀 | 功能测试 |
| lol_yolo.pt | ⭐⭐⭐⭐⭐ | 🚀🚀 | 实战使用 |

## 🔧 训练配置文件

### dataset.yaml
```yaml
# 数据集配置
path: ./training_data
train: images/train
val: images/val
test: images/test

# 类别
nc: 8
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

### 训练参数
```python
# 基础训练（快速）
epochs = 50
batch = 16
imgsz = 640

# 高质量训练（推荐）
epochs = 100
batch = 8
imgsz = 640
patience = 20  # 早停机制
```

## 📥 下载预训练模型（可选）

如果网络下载慢，可手动下载：

1. **YOLOv8n**: https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt
2. 放到用户目录: `C:\Users\<用户名>\.ultralytics\`

## 🎯 检测类别说明

### 1. champion_casting（英雄抬手）
- **关键特征**: 英雄施法前摇动作
- **标注要点**: 标注英雄整体，包括施法光效
- **应用**: 提前0.2-0.5秒预警敌方技能

### 2. enemy_champion（敌方英雄）
- **关键特征**: 小地图红色标记
- **标注要点**: 只标注小地图区域的敌人图标
- **应用**: 自动监控敌人位置

### 3. ally_champion（友方英雄）
- **关键特征**: 小地图蓝色标记
- **标注要点**: 只标注小地图区域的友军图标
- **应用**: 判断团队阵型

### 4. skillshot_indicator（技能指示器）
- **关键特征**: 地面范围标记、施法方向线
- **标注要点**: 标注完整的指示器区域
- **应用**: 辅助走位躲避

### 5. danger_ping（危险信号）
- **关键特征**: 红色叹号标记
- **标注要点**: 标注信号图标及周围效果
- **应用**: 高优先级警报

### 6. objective_spawn（目标刷新）
- **关键特征**: 大龙、小龙、峡谷等刷新提示
- **标注要点**: 标注刷新计时器或提示
- **应用**: 提醒打野时机

### 7. low_health（低血量）
- **关键特征**: 血条剩余<30%
- **标注要点**: 标注低血量的英雄头像或血条
- **应用**: 危险状态预警

### 8. enemy_ward（敌方眼位）
- **关键特征**: 敌方视野标记
- **标注要点**: 标注眼位图标
- **应用**: 提醒反眼

## 💡 标注技巧

### 数据收集建议
- 收集不同英雄的截图（至少10个英雄）
- 包含不同地图场景（召唤师峡谷、极地大乱斗）
- 包含白天/夜晚不同光照
- 包含对线/团战不同场景

### 标注质量要求
- 框选紧凑，尽量贴近目标边缘
- 避免包含过多背景
- 小目标也要标注（如小地图图标）
- 模糊或部分遮挡的目标也要标注

### 数据集划分
- 训练集: 70% (例如700张)
- 验证集: 20% (例如200张)
- 测试集: 10% (例如100张)

## 🚀 快速开始

### 最简单的方式
1. 先使用预训练模型测试功能
2. 收集50-100张游戏截图
3. 使用Roboflow在线标注（免费）
4. 下载YOLO格式数据集
5. 运行训练脚本
6. 将训练好的模型复制到此目录

### 预计时间
- 数据收集: 1-2小时（游戏中截图）
- 标注数据: 2-3小时（100张图）
- 训练模型: 30分钟-2小时（取决于硬件）

## 📚 参考资源

- **Ultralytics文档**: https://docs.ultralytics.com/
- **YOLO教程**: https://github.com/ultralytics/ultralytics
- **Roboflow教程**: https://blog.roboflow.com/how-to-train-yolov8/
- **LOLHelper文档**: `../CV_DETECTION_GUIDE.md`

---

**最后更新**: 2025-10-02  
**维护者**: LOLHelper Team
