"""
传统CV检测演示
实时显示检测结果，无需训练数据
"""

import cv2
import time
from services.traditional_cv_detector import TraditionalCVDetector


def demo_traditional_cv():
    """演示传统CV检测"""
    print("=" * 60)
    print("🎮 传统CV检测演示")
    print("=" * 60)
    print()
    print("💡 此演示不需要训练数据，立即可用！")
    print()
    print("📝 操作说明:")
    print("  - 确保LOL游戏正在运行")
    print("  - 脚本会每2秒检测一次")
    print("  - 按 Ctrl+C 退出")
    print()
    print("⏳ 开始检测...")
    print("=" * 60)
    print()
    
    detector = TraditionalCVDetector()
    
    try:
        iteration = 0
        while True:
            iteration += 1
            print(f"\n🔄 检测轮次 #{iteration}")
            print("-" * 60)
            
            start_time = time.time()
            
            # 1. 小地图敌人检测
            print("📍 检测小地图敌人...")
            enemies = detector.detect_minimap_enemies()
            print(f"   ✅ 发现 {len(enemies)} 个敌人")
            
            if enemies:
                for i, enemy in enumerate(enemies, 1):
                    print(f"      敌人{i}: 位置({enemy['x']:3d}, {enemy['y']:3d}) "
                          f"置信度:{enemy['confidence']:.2f} "
                          f"面积:{enemy['area']:.0f}")
            
            # 2. 血量检测
            print("\n❤️  检测血量状态...")
            health = detector.detect_low_health()
            health_percent = health['health_percent'] * 100
            
            if health['is_low']:
                print(f"   ⚠️  低血量警告！当前血量: {health_percent:.1f}%")
                print(f"      严重程度: {health['severity'].upper()}")
            else:
                print(f"   ✅ 血量正常: {health_percent:.1f}%")
            
            # 3. 危险信号检测
            print("\n⚠️  检测危险信号...")
            signals = detector.detect_danger_signals()
            print(f"   {'🚨 ' if signals else '✅'} 发现 {len(signals)} 个危险信号")
            
            if signals:
                for i, signal in enumerate(signals, 1):
                    print(f"      信号{i}: 位置({signal['x']:3d}, {signal['y']:3d}) "
                          f"置信度:{signal['confidence']:.2f}")
            
            # 4. 技能CD检测
            print("\n⚡ 检测技能CD...")
            skills = detector.detect_skill_cooldowns()
            cd_skills = [s for s in skills if s['on_cooldown']]
            
            print(f"   {'⏰' if cd_skills else '✅'} CD中的技能: {len(cd_skills)}/{len(skills)}")
            
            skill_names = ['Q', 'W', 'E', 'R', 'D', 'F']
            for skill in skills:
                if skill['slot'] < len(skill_names):
                    name = skill_names[skill['slot']]
                    status = "CD中" if skill['on_cooldown'] else "就绪"
                    brightness = skill['brightness']
                    print(f"      {name}: {status:4s} (亮度:{brightness:.0f})")
            
            # 5. 运动检测
            print("\n🏃 检测画面运动...")
            movement = detector.detect_champion_movement()
            
            if movement['movement_detected']:
                intensity = movement['intensity'] * 100
                print(f"   🎯 检测到运动 (强度:{intensity:.1f}%)")
            else:
                print(f"   ✅ 画面静止")
            
            # 统计
            elapsed = time.time() - start_time
            print()
            print(f"⏱️  检测耗时: {elapsed*1000:.0f}ms")
            print("-" * 60)
            
            # 等待
            time.sleep(2)
            
    except KeyboardInterrupt:
        print()
        print()
        print("=" * 60)
        print("👋 检测已停止")
        print("=" * 60)
        print()
        print(f"📊 总检测次数: {iteration}")
        print()
        print("💡 提示:")
        print("  - 如果检测结果不准确，可以调整颜色阈值")
        print("  - 编辑 services/traditional_cv_detector.py")
        print("  - 修改 self.color_ranges 中的颜色范围")
        print()
        print("📚 更多信息:")
        print("  - 查看 CV_METHODS_COMPARISON.md")
        print("  - 对比传统CV和YOLO的优缺点")
        print()


def save_detection_images():
    """保存检测结果图像（用于调试）"""
    print("=" * 60)
    print("📸 保存检测图像")
    print("=" * 60)
    print()
    
    detector = TraditionalCVDetector()
    
    # 确保目录存在
    import os
    os.makedirs("detections", exist_ok=True)
    
    regions = ['minimap', 'health_bar', 'skill_bar', 'danger_zone']
    
    for region_name in regions:
        region = detector.regions[region_name]
        img = detector.capture_screen(region)
        
        detector.save_debug_image(region_name, img)
    
    print()
    print("✅ 所有检测区域图像已保存到 detections/ 目录")
    print("💡 可以用这些图像调试参数")
    print()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--save-images':
        save_detection_images()
    else:
        demo_traditional_cv()
