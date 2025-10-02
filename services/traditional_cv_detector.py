"""
基于传统CV算法的游戏检测器
无需训练，使用图像处理技术直接检测

优点：
- 无需收集和标注训练数据
- 立即可用，无需等待训练
- 计算量小，速度快
- 对固定UI元素检测准确

缺点：
- 对动态内容（如英雄动作）检测有限
- 需要针对不同分辨率调整参数

适用场景：
- 小地图敌人检测（颜色识别）
- 技能CD检测（灰度识别）
- 血量检测（颜色+位置）
- 危险信号检测（颜色+形状）
"""

import cv2
import numpy as np
import mss
from datetime import datetime
import time


class TraditionalCVDetector:
    """传统CV检测器 - 无需训练"""
    
    def __init__(self):
        """初始化检测器"""
        self.screen_width = 1920
        self.screen_height = 1080
        
        # 颜色范围定义（HSV色彩空间）
        self.color_ranges = {
            'enemy_red': {
                'lower': np.array([0, 100, 100]),    # 敌方红色
                'upper': np.array([10, 255, 255])
            },
            'ally_blue': {
                'lower': np.array([100, 100, 100]),  # 友方蓝色
                'upper': np.array([130, 255, 255])
            },
            'danger_red': {
                'lower': np.array([0, 150, 150]),    # 危险标记红色
                'upper': np.array([10, 255, 255])
            },
            'skill_gold': {
                'lower': np.array([20, 100, 100]),   # 技能金色
                'upper': np.array([30, 255, 255])
            }
        }
        
        # 区域定义（相对坐标：left, top, right, bottom）
        self.regions = {
            'minimap': (0.85, 0.75, 1.0, 1.0),           # 小地图：右下角（修正）
            'health_bar': (0.0, 0.88, 0.25, 0.95),       # 血条：左下
            'skill_bar': (0.35, 0.85, 0.65, 1.0),        # 技能栏：底部中央
            'danger_zone': (0.25, 0.25, 0.75, 0.75),     # 危险区域：屏幕中央
        }
        
        print("✅ 传统CV检测器初始化完成")
        print("💡 无需训练，立即可用！")
    
    def capture_screen(self, region=None):
        """
        截取屏幕区域
        
        Args:
            region: (x1, y1, x2, y2) 相对坐标 0-1
        
        Returns:
            numpy.ndarray: BGR图像
        """
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            
            if region:
                x1, y1, x2, y2 = region
                capture_region = {
                    'left': int(monitor['left'] + x1 * monitor['width']),
                    'top': int(monitor['top'] + y1 * monitor['height']),
                    'width': int((x2 - x1) * monitor['width']),
                    'height': int((y2 - y1) * monitor['height'])
                }
            else:
                capture_region = monitor
            
            screenshot = sct.grab(capture_region)
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            return img
    
    def detect_minimap_enemies(self):
        """
        检测小地图敌人（基于颜色）
        
        原理：
        1. 截取小地图区域
        2. 转换到HSV色彩空间
        3. 查找红色区域（敌方颜色）
        4. 过滤噪声，返回敌人位置
        
        Returns:
            list: 敌人位置列表 [{'x', 'y', 'confidence'}, ...]
        """
        # 截取小地图
        minimap = self.capture_screen(self.regions['minimap'])
        
        # 转换到HSV
        hsv = cv2.cvtColor(minimap, cv2.COLOR_BGR2HSV)
        
        # 检测红色（敌方）
        mask = cv2.inRange(hsv, 
                          self.color_ranges['enemy_red']['lower'],
                          self.color_ranges['enemy_red']['upper'])
        
        # 形态学操作去噪
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        enemies = []
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # 过滤太小的区域（噪声）
            if area > 20:  # 最小面积阈值
                M = cv2.moments(contour)
                if M['m00'] != 0:
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00'])
                    
                    enemies.append({
                        'x': cx,
                        'y': cy,
                        'confidence': min(area / 100, 1.0),  # 面积越大越可信
                        'area': area
                    })
        
        return enemies
    
    def detect_low_health(self):
        """
        检测低血量状态（基于颜色+位置）
        
        原理：
        1. 截取血条区域
        2. 检测红色血条
        3. 计算血条长度占比
        4. 判断是否低于30%
        
        Returns:
            dict: {'is_low': bool, 'health_percent': float}
        """
        health_region = self.capture_screen(self.regions['health_bar'])
        
        # 转换到HSV
        hsv = cv2.cvtColor(health_region, cv2.COLOR_BGR2HSV)
        
        # 检测绿色（高血量）和红色（低血量）
        green_mask = cv2.inRange(hsv, np.array([40, 50, 50]), 
                                      np.array([80, 255, 255]))
        red_mask = cv2.inRange(hsv, np.array([0, 100, 100]), 
                                    np.array([10, 255, 255]))
        
        green_pixels = cv2.countNonZero(green_mask)
        red_pixels = cv2.countNonZero(red_mask)
        
        total_health_pixels = green_pixels + red_pixels
        
        if total_health_pixels > 0:
            health_percent = green_pixels / total_health_pixels
        else:
            health_percent = 1.0
        
        return {
            'is_low': health_percent < 0.3,
            'health_percent': health_percent,
            'severity': 'high' if health_percent < 0.2 else 'medium' if health_percent < 0.4 else 'low'
        }
    
    def detect_danger_signals(self):
        """
        检测危险信号标记（基于颜色+形状）
        
        原理：
        1. 截取游戏中央区域
        2. 检测红色叹号形状
        3. 使用模板匹配或轮廓检测
        
        Returns:
            list: 危险信号列表
        """
        danger_region = self.capture_screen(self.regions['danger_zone'])
        
        # 转换到HSV
        hsv = cv2.cvtColor(danger_region, cv2.COLOR_BGR2HSV)
        
        # 检测亮红色
        mask = cv2.inRange(hsv,
                          self.color_ranges['danger_red']['lower'],
                          self.color_ranges['danger_red']['upper'])
        
        # 形态学操作
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        signals = []
        for contour in contours:
            area = cv2.contourArea(contour)
            
            if area > 100:  # 最小面积
                x, y, w, h = cv2.boundingRect(contour)
                
                # 简单的形状检测（叹号通常是高瘦的）
                aspect_ratio = h / w if w > 0 else 0
                
                if 1.5 < aspect_ratio < 5:  # 叹号的宽高比
                    signals.append({
                        'x': x + w // 2,
                        'y': y + h // 2,
                        'confidence': min(area / 500, 1.0),
                        'type': 'danger_ping'
                    })
        
        return signals
    
    def detect_skill_cooldowns(self):
        """
        检测技能CD（基于灰度）
        
        原理：
        1. 截取技能栏区域
        2. 检测灰度区域（CD中的技能）
        3. 识别哪些技能可用/CD中
        
        Returns:
            list: 技能状态列表
        """
        skill_region = self.capture_screen(self.regions['skill_bar'])
        
        # 转换为灰度图
        gray = cv2.cvtColor(skill_region, cv2.COLOR_BGR2GRAY)
        
        # 技能按钮通常是方形，均匀分布
        height, width = gray.shape
        skill_width = width // 6  # 假设有6个技能槽（QWER+召唤师技能）
        
        skills = []
        for i in range(6):
            x_start = i * skill_width
            x_end = (i + 1) * skill_width
            
            skill_area = gray[:, x_start:x_end]
            
            # 计算平均亮度
            avg_brightness = np.mean(skill_area)
            
            # CD中的技能会更暗（有灰色遮罩）
            is_on_cooldown = avg_brightness < 100  # 亮度阈值
            
            skills.append({
                'slot': i,
                'on_cooldown': is_on_cooldown,
                'brightness': float(avg_brightness)
            })
        
        return skills
    
    def detect_champion_movement(self):
        """
        检测英雄移动（基于帧差法）
        
        原理：
        1. 连续捕获两帧
        2. 计算帧差
        3. 检测运动区域
        
        注意：需要维护上一帧的图像
        
        Returns:
            dict: 运动信息
        """
        # 这需要维护状态，这里提供简化版本
        center_region = self.capture_screen((0.4, 0.4, 0.6, 0.6))
        
        # 转换为灰度
        gray = cv2.cvtColor(center_region, cv2.COLOR_BGR2GRAY)
        
        # 检测边缘（移动物体通常有明显边缘）
        edges = cv2.Canny(gray, 50, 150)
        
        # 计算边缘密度
        edge_density = np.count_nonzero(edges) / edges.size
        
        return {
            'movement_detected': edge_density > 0.05,
            'intensity': edge_density
        }
    
    def comprehensive_detection(self):
        """
        综合检测 - 整合所有检测方法
        
        Returns:
            dict: 完整的检测结果
        """
        try:
            results = {
                'timestamp': time.time(),
                'minimap_enemies': self.detect_minimap_enemies(),
                'health_status': self.detect_low_health(),
                'danger_signals': self.detect_danger_signals(),
                'skill_status': self.detect_skill_cooldowns(),
                'movement': self.detect_champion_movement()
            }
            
            return results
            
        except Exception as e:
            print(f"❌ 检测失败: {e}")
            return None
    
    def save_debug_image(self, region_name, img):
        """保存调试图像"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"debug_{region_name}_{timestamp}.jpg"
        cv2.imwrite(f"detections/{filename}", img)
        print(f"💾 调试图像保存: {filename}")


# 全局检测器实例
_traditional_detector = None


def get_traditional_detector():
    """获取全局检测器实例"""
    global _traditional_detector
    if _traditional_detector is None:
        _traditional_detector = TraditionalCVDetector()
    return _traditional_detector


if __name__ == '__main__':
    """测试代码"""
    print("🧪 测试传统CV检测器")
    print()
    
    detector = TraditionalCVDetector()
    
    print("开始检测...")
    print("=" * 60)
    
    # 测试小地图敌人检测
    print("\n1️⃣ 小地图敌人检测:")
    enemies = detector.detect_minimap_enemies()
    print(f"   发现 {len(enemies)} 个敌人")
    for i, enemy in enumerate(enemies, 1):
        print(f"   敌人{i}: 位置({enemy['x']}, {enemy['y']}) 置信度:{enemy['confidence']:.2f}")
    
    # 测试血量检测
    print("\n2️⃣ 血量检测:")
    health = detector.detect_low_health()
    print(f"   血量: {health['health_percent']*100:.1f}%")
    print(f"   低血量: {'是' if health['is_low'] else '否'}")
    print(f"   严重程度: {health['severity']}")
    
    # 测试危险信号
    print("\n3️⃣ 危险信号检测:")
    signals = detector.detect_danger_signals()
    print(f"   发现 {len(signals)} 个危险信号")
    
    # 测试技能CD
    print("\n4️⃣ 技能CD检测:")
    skills = detector.detect_skill_cooldowns()
    cd_count = sum(1 for s in skills if s['on_cooldown'])
    print(f"   CD中的技能: {cd_count}/{len(skills)}")
    
    print()
    print("=" * 60)
    print("✅ 测试完成")
