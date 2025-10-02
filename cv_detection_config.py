"""
CV检测配置文件
可以在这里调整检测参数和行为
"""

# ============================================================
# 检测模式配置
# ============================================================

# 是否启用传统CV检测（False则只使用YOLO）
USE_TRADITIONAL_CV = True

# 是否启用YOLO检测（False则只使用传统CV）
USE_YOLO = True

# 检测间隔（秒）
DETECTION_INTERVAL = 1.0

# ============================================================
# 传统CV检测参数
# ============================================================

# 小地图敌人检测 - 红色标记的HSV范围
MINIMAP_ENEMY_COLOR_RANGES = [
    # 红色范围1 (偏橙红)
    {'lower': (0, 100, 100), 'upper': (10, 255, 255)},
    # 红色范围2 (偏紫红)
    {'lower': (170, 100, 100), 'upper': (180, 255, 255)}
]

# 小地图区域 (相对坐标: left, top, right, bottom)
# 修正：LOL小地图在右下角，不是左下角
MINIMAP_REGION = {
    'left': 0.85,
    'top': 0.75,
    'right': 1.0,
    'bottom': 1.0
}

# 敌人标记最小面积（像素）
MINIMAP_MIN_AREA = 5

# 敌人标记最大面积（像素）
MINIMAP_MAX_AREA = 200

# ============================================================
# 血量检测参数
# ============================================================

# 血条区域 (相对坐标)
HEALTH_BAR_REGION = {
    'left': 0.4,
    'top': 0.9,
    'right': 0.6,
    'bottom': 0.95
}

# 低血量阈值（百分比）
LOW_HEALTH_THRESHOLD = 30

# 危险血量阈值（百分比）
CRITICAL_HEALTH_THRESHOLD = 15

# 绿色血条HSV范围
HEALTH_GREEN_RANGE = {
    'lower': (40, 50, 50),
    'upper': (80, 255, 255)
}

# 红色背景HSV范围（缺失的血量）
HEALTH_RED_RANGE = {
    'lower': (0, 50, 50),
    'upper': (10, 255, 255)
}

# ============================================================
# 危险信号检测参数
# ============================================================

# 危险信号区域 (相对坐标)
DANGER_SIGNAL_REGION = {
    'left': 0.3,
    'top': 0.3,
    'right': 0.7,
    'bottom': 0.7
}

# 红色危险信号HSV范围
DANGER_RED_RANGE = {
    'lower': (0, 150, 150),
    'upper': (10, 255, 255)
}

# 黄色警告信号HSV范围
DANGER_YELLOW_RANGE = {
    'lower': (20, 100, 100),
    'upper': (30, 255, 255)
}

# 危险信号最小面积
DANGER_MIN_AREA = 100

# 危险信号纵横比范围 (width/height)
DANGER_ASPECT_RATIO_MIN = 0.5
DANGER_ASPECT_RATIO_MAX = 2.0

# ============================================================
# 技能冷却检测参数
# ============================================================

# 技能栏区域 (相对坐标)
SKILL_BAR_REGION = {
    'left': 0.35,
    'top': 0.85,
    'right': 0.65,
    'bottom': 0.95
}

# 技能数量
SKILL_COUNT = 6  # Q, W, E, R, D, F

# 冷却中的技能亮度阈值（灰度值，0-255）
SKILL_COOLDOWN_BRIGHTNESS_THRESHOLD = 50

# ============================================================
# YOLO检测参数
# ============================================================

# YOLO模型路径
YOLO_MODEL_PATH = "models/lol_yolo.pt"

# YOLO置信度阈值
YOLO_CONFIDENCE_THRESHOLD = 0.5

# YOLO检测的目标类别
YOLO_TARGET_CLASSES = [
    'champion_casting',      # 英雄施法动作
    'skillshot_indicator',   # 技能指示器
]

# ============================================================
# 性能优化配置
# ============================================================

# 是否启用调试模式（保存检测图像）
DEBUG_MODE = False

# 调试图像保存路径
DEBUG_IMAGE_PATH = "debug_images"

# 截图分辨率缩放（1.0 = 原始分辨率）
SCREENSHOT_SCALE = 1.0

# ============================================================
# 警报配置
# ============================================================

# 是否启用警报
ENABLE_ALERTS = True

# 警报类型配置
ALERTS_CONFIG = {
    'champion_casting': {
        'enabled': True,
        'severity': 'medium',
        'message': '⚠️ 检测到英雄施法动作！'
    },
    'minimap_enemies': {
        'enabled': True,
        'severity': 'high',
        'message': '🚨 小地图发现敌人！'
    },
    'low_health': {
        'enabled': True,
        'severity': 'high',
        'message': '⚠️ 血量过低！'
    },
    'danger_signals': {
        'enabled': True,
        'severity': 'high',
        'message': '🚨 检测到危险信号！'
    },
    'skill_cooldown': {
        'enabled': False,  # 技能冷却警报默认关闭
        'severity': 'low',
        'message': 'ℹ️ 技能冷却中'
    }
}

# ============================================================
# 实验性功能
# ============================================================

# 是否使用多线程检测
USE_MULTITHREADING = False

# 是否使用GPU加速（需要CUDA）
USE_GPU = False

# ============================================================
# 配置验证函数
# ============================================================

def validate_config():
    """验证配置参数的有效性"""
    errors = []
    
    # 检查检测模式
    if not USE_TRADITIONAL_CV and not USE_YOLO:
        errors.append("至少需要启用一种检测模式（传统CV或YOLO）")
    
    # 检查阈值范围
    if not (0 < LOW_HEALTH_THRESHOLD <= 100):
        errors.append(f"LOW_HEALTH_THRESHOLD 必须在 0-100 之间，当前值: {LOW_HEALTH_THRESHOLD}")
    
    if not (0 < CRITICAL_HEALTH_THRESHOLD <= LOW_HEALTH_THRESHOLD):
        errors.append(f"CRITICAL_HEALTH_THRESHOLD 必须小于 LOW_HEALTH_THRESHOLD")
    
    # 检查区域坐标
    for region_name, region in [
        ('MINIMAP_REGION', MINIMAP_REGION),
        ('HEALTH_BAR_REGION', HEALTH_BAR_REGION),
        ('DANGER_SIGNAL_REGION', DANGER_SIGNAL_REGION),
        ('SKILL_BAR_REGION', SKILL_BAR_REGION)
    ]:
        if not (0 <= region['left'] < region['right'] <= 1):
            errors.append(f"{region_name} 水平坐标无效")
        if not (0 <= region['top'] < region['bottom'] <= 1):
            errors.append(f"{region_name} 垂直坐标无效")
    
    if errors:
        print("⚠️ 配置错误:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("✅ 配置验证通过")
    return True


def print_config_summary():
    """打印配置摘要"""
    print("\n" + "=" * 60)
    print("📋 CV检测配置摘要")
    print("=" * 60)
    
    # 检测模式
    mode = []
    if USE_TRADITIONAL_CV:
        mode.append("传统CV")
    if USE_YOLO:
        mode.append("YOLO")
    print(f"\n🎯 检测模式: {' + '.join(mode)}")
    print(f"⏱️  检测间隔: {DETECTION_INTERVAL}秒")
    
    # 传统CV参数
    if USE_TRADITIONAL_CV:
        print("\n🔍 传统CV参数:")
        print(f"   - 小地图敌人最小面积: {MINIMAP_MIN_AREA}px")
        print(f"   - 低血量阈值: {LOW_HEALTH_THRESHOLD}%")
        print(f"   - 危险血量阈值: {CRITICAL_HEALTH_THRESHOLD}%")
        print(f"   - 技能数量: {SKILL_COUNT}")
    
    # YOLO参数
    if USE_YOLO:
        print("\n🎯 YOLO参数:")
        print(f"   - 模型路径: {YOLO_MODEL_PATH}")
        print(f"   - 置信度阈值: {YOLO_CONFIDENCE_THRESHOLD}")
        print(f"   - 目标类别: {', '.join(YOLO_TARGET_CLASSES)}")
    
    # 警报配置
    enabled_alerts = [k for k, v in ALERTS_CONFIG.items() if v['enabled']]
    print(f"\n🚨 警报状态: {'启用' if ENABLE_ALERTS else '禁用'}")
    if ENABLE_ALERTS:
        print(f"   已启用警报: {', '.join(enabled_alerts)}")
    
    # 调试模式
    if DEBUG_MODE:
        print(f"\n🐛 调试模式: 已启用 (图像保存至 {DEBUG_IMAGE_PATH})")
    
    print("=" * 60 + "\n")


if __name__ == "__main__":
    # 验证并打印配置
    if validate_config():
        print_config_summary()
