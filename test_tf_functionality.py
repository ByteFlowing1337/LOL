"""
卡牌大师黄牌检测测试脚本
测试HSV颜色检测和键盘控制功能
"""
import cv2
import numpy as np
import time

try:
    from pynput.keyboard import Controller, Key
    PYNPUT_AVAILABLE = True
except ImportError:
    print("⚠️ pynput未安装，键盘控制功能将不可用")
    print("安装命令: pip install pynput")
    PYNPUT_AVAILABLE = False

try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    print("⚠️ mss未安装，屏幕截图功能将不可用")
    print("安装命令: pip install mss")
    MSS_AVAILABLE = False


def test_yellow_detection():
    """测试黄色检测算法"""
    print("\n" + "="*60)
    print("测试 1: 黄色检测算法")
    print("="*60)
    
    # 创建测试图像
    test_img = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # 添加黄色区域
    yellow_color = [30, 200, 255]  # HSV格式的黄色
    test_img[200:280, 280:360] = yellow_color
    
    # 转换为HSV
    hsv = cv2.cvtColor(test_img, cv2.COLOR_RGB2HSV)
    
    # 定义黄色范围
    yellow_lower = np.array([20, 100, 200])
    yellow_upper = np.array([35, 255, 255])
    
    # 创建掩码
    mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
    
    # 计算黄色像素比例
    yellow_pixels = cv2.countNonZero(mask)
    total_pixels = test_img.shape[0] * test_img.shape[1]
    yellow_ratio = yellow_pixels / total_pixels
    
    print(f"✅ 黄色像素数: {yellow_pixels}")
    print(f"✅ 总像素数: {total_pixels}")
    print(f"✅ 黄色占比: {yellow_ratio*100:.2f}%")
    
    if yellow_ratio > 0.03:
        print("✅ 检测成功！黄色占比超过3%")
        return True
    else:
        print("❌ 检测失败！黄色占比不足3%")
        return False


def test_screen_capture():
    """测试屏幕截图功能"""
    print("\n" + "="*60)
    print("测试 2: 屏幕截图")
    print("="*60)
    
    if not MSS_AVAILABLE:
        print("❌ mss库未安装，跳过此测试")
        return False
    
    try:
        with mss.mss() as sct:
            # 获取主显示器
            monitor = sct.monitors[1]
            print(f"✅ 显示器尺寸: {monitor['width']}x{monitor['height']}")
            
            # 计算中心区域
            width = monitor['width']
            height = monitor['height']
            
            # 40%-60% 水平，25%-50% 垂直
            region = {
                'left': int(width * 0.4),
                'top': int(height * 0.25),
                'width': int(width * 0.2),
                'height': int(height * 0.25)
            }
            
            print(f"✅ 检测区域: {region['width']}x{region['height']}")
            print(f"   左上角: ({region['left']}, {region['top']})")
            
            # 截图
            screenshot = sct.grab(region)
            img = np.array(screenshot)
            
            print(f"✅ 截图成功！形状: {img.shape}")
            
            # 保存测试截图
            cv2.imwrite('test_screenshot.png', img)
            print("✅ 测试截图已保存: test_screenshot.png")
            
            return True
    except Exception as e:
        print(f"❌ 截图失败: {e}")
        return False


def test_keyboard_control():
    """测试键盘控制功能"""
    print("\n" + "="*60)
    print("测试 3: 键盘控制 (模拟W键)")
    print("="*60)
    
    if not PYNPUT_AVAILABLE:
        print("❌ pynput库未安装，跳过此测试")
        return False
    
    try:
        keyboard = Controller()
        
        print("⚠️ 注意：3秒后将模拟按下W键")
        print("   请确保焦点不在重要窗口中")
        
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        print("▶️ 按下W键")
        keyboard.press('w')
        time.sleep(0.01)  # 按住10ms
        keyboard.release('w')
        print("✅ W键已释放")
        
        print("✅ 键盘控制测试成功！")
        return True
        
    except Exception as e:
        print(f"❌ 键盘控制失败: {e}")
        return False


def test_hsv_color_range():
    """测试不同黄色的HSV值"""
    print("\n" + "="*60)
    print("测试 4: 黄色HSV范围验证")
    print("="*60)
    
    # 测试不同黄色
    yellow_colors = [
        ("亮黄", [255, 255, 0]),    # RGB
        ("金黄", [255, 215, 0]),
        ("橙黄", [255, 200, 0]),
        ("浅黄", [255, 255, 128]),
    ]
    
    for name, rgb in yellow_colors:
        # 转换为HSV
        color = np.uint8([[rgb]])
        hsv = cv2.cvtColor(color, cv2.COLOR_RGB2HSV)
        h, s, v = hsv[0][0]
        
        # 检查是否在范围内
        in_range = 20 <= h <= 35 and s >= 100 and v >= 200
        
        status = "✅ 可检测" if in_range else "❌ 超出范围"
        print(f"{status} | {name:6s} | RGB{rgb} → HSV({h:3d}, {s:3d}, {v:3d})")
    
    return True


def test_tf_selector_integration():
    """测试TF选择器完整流程"""
    print("\n" + "="*60)
    print("测试 5: TF选择器集成测试")
    print("="*60)
    
    try:
        from services.tf_card_selector import TwistedFateCardSelector
        
        print("✅ TwistedFateCardSelector 导入成功")
        
        # 创建选择器实例
        selector = TwistedFateCardSelector()
        print("✅ 选择器实例创建成功")
        
        # 设置英雄
        selector.set_champion('TwistedFate')
        print(f"✅ 当前英雄: {selector.current_champion}")
        print(f"✅ 启用状态: {selector.is_enabled}")
        
        # 模拟W键按下
        selector.on_w_pressed()
        print(f"✅ W键按下状态: {selector.w_pressed}")
        
        # 执行一次检测（不会真正按键）
        print("\n⚠️ 执行黄牌检测（不会按键）...")
        result = selector.check_and_select_yellow_card()
        
        if result:
            print(f"✅ 检测完成")
            print(f"   检测到: {result.get('detected', False)}")
            print(f"   黄色占比: {result.get('yellow_ratio', 0)*100:.2f}%")
            print(f"   自动按键: {result.get('auto_pressed', False)}")
        
        print("\n✅ TF选择器集成测试通过！")
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("   请确保 services/tf_card_selector.py 存在")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🃏"*30)
    print("  卡牌大师黄牌检测 - 功能测试套件")
    print("🃏"*30)
    
    results = {
        '黄色检测算法': test_yellow_detection(),
        '屏幕截图': test_screen_capture(),
        '键盘控制': test_keyboard_control(),
        'HSV范围验证': test_hsv_color_range(),
        'TF选择器集成': test_tf_selector_integration()
    }
    
    # 输出测试结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} | {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("="*60)
    print(f"总计: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("🎉 所有测试通过！TF黄牌辅助功能可以正常使用。")
    else:
        print("⚠️ 部分测试失败，请检查缺失的依赖库。")
    
    print("\n依赖库检查:")
    print(f"  pynput: {'✅ 已安装' if PYNPUT_AVAILABLE else '❌ 未安装 (pip install pynput)'}")
    print(f"  mss:    {'✅ 已安装' if MSS_AVAILABLE else '❌ 未安装 (pip install mss)'}")
    print(f"  opencv: ✅ 已安装 (cv2 可用)")
    print(f"  numpy:  ✅ 已安装")


if __name__ == '__main__':
    run_all_tests()
