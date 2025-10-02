# 📖 LOLHelper - 完整功能说明

## 🎮 项目简介

LOLHelper是一个功能强大的英雄联盟辅助工具，提供战绩查询、自动化功能和AI视觉检测。

**版本**: v2.1.1  
**更新日期**: 2025-10-02

---

## ✨ 核心功能

### 1️⃣ 战绩查询系统
- 📊 **召唤师战绩查询**: 输入召唤师名称，查看最近战绩
- 🔗 **详细战绩页面**: 点击召唤师名称查看完整历史数据
- 📈 **统计分析**: KDA、胜率、常用英雄统计

### 2️⃣ 自动化功能
- ✅ **自动接受对局**: 匹配成功自动接受
- 📊 **敌我数据分析**: 选人阶段自动分析队友和敌人战绩
- ⚡ **实时游戏监控**: 独立页面显示当前游戏详细信息

### 3️⃣ CV视觉检测（🆕 v2.1.0）
- 🎯 **英雄抬手检测**: 提前0.2-0.5秒识别施法动作
- 🗺️ **小地图监控**: 自动识别敌方英雄位置
- ⚠️ **危险信号检测**: 低血量、危险标记识别
- ⚡ **技能指示器识别**: 辅助走位躲避技能

---

## 🚀 快速开始

### 安装依赖

#### 基础功能
```bash
pip install flask flask-socketio requests psutil chardet
```

#### CV检测功能
```powershell
.\install_cv_deps.ps1
```

或手动安装：
```bash
pip install opencv-python numpy mss ultralytics
```

### 启动应用

```bash
python app_new.py
```

浏览器访问: http://localhost:5000

---

## 📚 详细文档

| 文档 | 说明 |
|-----|------|
| [QUICKSTART_CV.md](QUICKSTART_CV.md) | CV检测快速入门 |
| [CV_DETECTION_GUIDE.md](CV_DETECTION_GUIDE.md) | CV检测完整指南 |
| [UPDATE_LOG.md](UPDATE_LOG.md) | 版本更新日志 |
| [BUGFIX_LOG.md](BUGFIX_LOG.md) | Bug修复记录 |
| [models/README.md](models/README.md) | YOLO模型说明 |

---

## 🎯 功能详解

### 战绩查询

**使用方法：**
1. 主页输入召唤师名称（格式：`名称#TAG`）
2. 点击"获取战绩"按钮
3. 查看最近对局记录

**功能特性：**
- 显示英雄、KDA、胜负、时长
- 支持点击召唤师名称跳转详情页
- 自动识别游戏模式（排位/匹配/大乱斗等）

### 自动接受对局

**使用方法：**
1. 点击"自动接受对局"按钮
2. 开始匹配
3. 匹配成功后自动接受

**注意事项：**
- 需要游戏客户端处于运行状态
- LCU连接状态需显示"已连接"

### 敌我分析

**使用方法：**
1. 进入选人阶段
2. 点击"敌我分析"按钮
3. 查看队友和敌人的战绩分析

**分析内容：**
- 最近胜率
- 常用英雄
- KDA统计
- 熟练度评估

### CV视觉检测

**快速开始：**
1. 访问: http://localhost:5000/vision_detection
2. 点击"开始检测"按钮
3. 观察检测结果和警报

**详细说明：**
参考 [QUICKSTART_CV.md](QUICKSTART_CV.md)

---

## 🛠️ 技术架构

### 后端技术栈
- **Python 3.8+**: 核心语言
- **Flask 2.3+**: Web框架
- **Flask-SocketIO 5.3+**: WebSocket实时通信
- **OpenCV 4.8+**: 图像处理（CV功能）
- **Ultralytics YOLO 8.0+**: 目标检测（CV功能）

### 前端技术栈
- **Bootstrap 5.3.3**: UI框架
- **Socket.IO Client 4.7.5**: 实时通信
- **Bootstrap Icons 1.11.3**: 图标库

### API集成
- **LCU API**: 游戏客户端API（动态端口）
- **Game Client API**: 游戏内API（端口2999）

### 项目结构

```
LOLHelperWeb/
├── app_new.py                 # 主应用入口
├── config.py                  # 配置文件
├── constants.py               # 常量定义
├── lcu_api.py                 # LCU API封装
│
├── routes/                    # 路由模块
│   └── api_routes.py          # HTTP路由
│
├── services/                  # 服务模块
│   ├── game_vision.py         # CV检测引擎
│   └── vision_service.py      # CV检测服务
│
├── utils/                     # 工具模块
│   └── game_data_formatter.py # 数据格式化
│
├── websocket/                 # WebSocket模块
│   └── socket_events.py       # Socket事件处理
│
├── templates/                 # HTML模板
│   ├── index.html             # 主页
│   ├── summoner_detail.html   # 召唤师详情
│   ├── live_game.html         # 实时游戏
│   └── vision_detection.html  # CV检测
│
├── static/                    # 静态资源
│   └── js/
│       └── main.js            # 前端脚本
│
├── models/                    # YOLO模型
│   └── README.md              # 模型说明
│
├── tools/                     # 工具脚本
│   ├── collect_training_data.py   # 数据收集
│   └── train_yolo_model.py        # 模型训练
│
└── docs/                      # 文档
    ├── QUICKSTART_CV.md       # CV快速入门
    ├── CV_DETECTION_GUIDE.md  # CV完整指南
    ├── UPDATE_LOG.md          # 更新日志
    └── BUGFIX_LOG.md          # Bug修复
```

---

## ❓ 常见问题

### Q1: LCU连接失败
**问题**: 显示"LCU连接失败"或"端口未找到"

**解决方案**:
1. 确认游戏客户端正在运行
2. 以管理员身份运行应用
3. 检查防火墙设置
4. 重启游戏客户端

### Q2: 战绩查询无结果
**问题**: 输入召唤师名称后无返回

**解决方案**:
1. 确认名称格式正确（`名称#TAG`）
2. 检查网络连接
3. 确认LCU连接状态为"已连接"
4. 查看控制台错误信息

### Q3: CV检测不准确
**问题**: 误检或漏检严重

**解决方案**:
1. 当前使用的是通用预训练模型
2. 建议训练LOL专用模型（参考 models/README.md）
3. 调整置信度阈值
4. 收集更多训练数据

### Q4: CV检测时游戏卡顿
**问题**: 启动检测后游戏FPS下降

**解决方案**:
1. 增加检测间隔（改为2秒）
2. 降低检测分辨率
3. 使用GPU加速
4. 关闭其他占用资源的程序

### Q5: 模型训练失败
**问题**: 运行训练脚本报错

**解决方案**:
1. 确认数据集目录结构正确
2. 检查图片和标签文件配对
3. 验证dataset.yaml配置
4. 查看完整错误日志

---

## 🔧 配置说明

### 修改检测频率

编辑 `services/vision_service.py`:
```python
vision_detection_task(socketio, detection_interval=1.0)  # 改为2.0更省资源
```

### 修改检测区域

编辑 `services/game_vision.py`:
```python
self.regions = {
    'minimap': {'x': 0, 'y': 0.75, 'width': 0.15, 'height': 0.25},
    # 调整x, y, width, height值
}
```

### 修改置信度阈值

在检测函数中调整:
```python
results = detector.detect_objects(img, confidence_threshold=0.5)  # 0.3-0.7
```

---

## 📊 性能参考

### 系统要求

**最低配置:**
- CPU: Intel i5 / AMD Ryzen 5
- 内存: 8GB
- Python: 3.8+

**推荐配置:**
- CPU: Intel i7 / AMD Ryzen 7
- 内存: 16GB
- 显卡: GTX 1660+（用于GPU加速）
- Python: 3.10+

### 性能指标

| 功能 | CPU占用 | 内存占用 | 网络流量 |
|-----|--------|---------|---------|
| 战绩查询 | ~5% | ~100MB | 低 |
| 自动化功能 | ~10% | ~150MB | 中 |
| CV检测（CPU） | ~30-50% | ~500MB | 无 |
| CV检测（GPU） | ~10% | ~800MB | 无 |

---

## 🎓 进阶使用

### 训练自定义YOLO模型

**步骤1: 收集数据**
```bash
python tools/collect_training_data.py
```

**步骤2: 标注数据**
- 使用Roboflow或LabelImg
- 标注8个类别（见models/README.md）

**步骤3: 训练模型**
```bash
python tools/train_yolo_model.py
```

**详细教程**: [models/README.md](models/README.md)

### GPU加速

**安装CUDA版PyTorch:**
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

YOLO会自动检测并使用GPU。

### 部署到服务器

**使用Waitress（生产环境）:**
```bash
pip install waitress
```

修改 `app_new.py`:
```python
from waitress import serve
serve(app, host='0.0.0.0', port=5000)
```

---

## 🤝 贡献指南

欢迎提交问题和改进建议！

**提交Bug报告时请包含:**
1. 错误截图或日志
2. Python版本
3. 操作系统版本
4. 复现步骤

**提交功能建议时请说明:**
1. 功能描述
2. 使用场景
3. 预期效果

---

## 📜 版本历史

### v2.1.1 (2025-10-02)
- 🐛 修复CV检测线程安全问题
- 📝 添加完整文档和训练工具

### v2.1.0 (2025-10-02)
- 🎥 新增YOLO视觉检测功能
- 📊 添加实时检测仪表盘
- ⚠️ 添加智能警报系统

### v2.0.0 (2025-10-01)
- 📊 增强数据展示
- 🔗 添加召唤师详情页
- 📺 添加实时游戏监控

### v1.0.0
- 🎮 基础战绩查询
- ✅ 自动接受对局
- 📊 敌我分析

---

## 📞 技术支持

**项目地址**: https://github.com/ByteFlowing1337/LOL

**问题反馈**: 提交Issue到GitHub

**文档更新**: 2025-10-02

---

## 📄 许可证

MIT License

---

**🎉 祝您使用愉快！召唤师峡谷见！**
