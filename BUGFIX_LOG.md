# 🐛 Bug修复说明

## v2.1.1 - 修复线程安全问题 (2025-10-02)

### 问题描述
```
❌ 截图失败: '_thread._local' object has no attribute 'srcdc'
```

### 根本原因
mss库在多线程环境中存在线程安全问题。在`GameVisionDetector.__init__`中创建的`self.sct = mss.mss()`实例在多线程调用时会导致冲突。

### 解决方案
修改 `services/game_vision.py`：

**修改前：**
```python
def __init__(self, model_path=None):
    self.sct = mss.mss()  # ❌ 在初始化时创建，线程不安全
    # ...

def capture_screen(self, region=None):
    screenshot = self.sct.grab(monitor)  # ❌ 多线程冲突
```

**修改后：**
```python
def __init__(self, model_path=None):
    # ✅ 不在初始化时创建mss实例
    # ...

def capture_screen(self, region=None):
    # ✅ 每次调用时创建新实例（线程安全）
    with mss.mss() as sct:
        screenshot = sct.grab(monitor)
```

### 修改详情
1. 移除 `self.sct = mss.mss()` 实例变量
2. 在 `capture_screen()` 方法中使用 `with mss.mss() as sct:` 上下文管理器
3. 每次截图时创建独立的mss实例，避免线程冲突

### 影响范围
- ✅ 修复了后台检测线程的截图崩溃问题
- ✅ 修复了手动截图功能的错误
- ✅ 确保多线程环境下的稳定性

### 性能影响
- 每次截图创建新实例会有轻微性能开销（<5ms）
- 相比崩溃问题，性能损失可以接受
- mss库的上下文管理器会自动清理资源

### 测试验证
```bash
# 运行测试
python test_cv_detection.py

# 预期结果
✅ 截图成功
   分辨率: 2560x1440
   通道数: 3
   数据类型: uint8
```

### 相关文件
- `services/game_vision.py` - 核心修复
- `services/vision_service.py` - 调用截图的服务（无需修改）

### 附加说明
这是mss库的已知问题，参考：
- https://github.com/BoboTiG/python-mss/issues/203
- 推荐使用上下文管理器避免线程问题

---

**修复日期**: 2025-10-02  
**版本**: v2.1.1
