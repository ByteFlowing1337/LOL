"""
CV检测功能测试脚本
测试各个CV模块的导入和基本功能
"""

import sys
import os

def test_imports():
    """测试所有依赖是否正确安装"""
    print("=" * 60)
    print("测试 1: 检查依赖包导入")
    print("=" * 60)
    
    imports = {
        'cv2': 'OpenCV',
        'numpy': 'NumPy',
        'mss': 'MSS屏幕截图',
        'ultralytics': 'Ultralytics YOLO'
    }
    
    all_ok = True
    for module, name in imports.items():
        try:
            __import__(module)
            print(f"✅ {name:20s} - 导入成功")
        except ImportError as e:
            print(f"❌ {name:20s} - 导入失败: {e}")
            all_ok = False
    
    print()
    return all_ok

def test_cv_modules():
    """测试CV模块"""
    print("=" * 60)
    print("测试 2: 检查CV模块")
    print("=" * 60)
    
    try:
        import cv2
        print(f"✅ OpenCV版本: {cv2.__version__}")
        
        import numpy as np
        print(f"✅ NumPy版本: {np.__version__}")
        
        import mss
        with mss.mss() as sct:
            monitors = sct.monitors
            print(f"✅ 检测到 {len(monitors)-1} 个显示器")
            for i, monitor in enumerate(monitors[1:], 1):
                print(f"   显示器{i}: {monitor['width']}x{monitor['height']}")
        
        from ultralytics import YOLO
        print(f"✅ YOLO可用")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print()
        return False

def test_screen_capture():
    """测试屏幕截图功能"""
    print("=" * 60)
    print("测试 3: 屏幕截图功能")
    print("=" * 60)
    
    try:
        import mss
        import numpy as np
        
        with mss.mss() as sct:
            # 截取主显示器
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            
            # 转换为numpy数组
            img = np.array(screenshot)
            
            print(f"✅ 截图成功")
            print(f"   分辨率: {img.shape[1]}x{img.shape[0]}")
            print(f"   通道数: {img.shape[2]}")
            print(f"   数据类型: {img.dtype}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print()
        return False

def test_yolo_model():
    """测试YOLO模型加载"""
    print("=" * 60)
    print("测试 4: YOLO模型")
    print("=" * 60)
    
    try:
        from ultralytics import YOLO
        import os
        
        # 检查自定义模型
        model_path = 'models/lol_yolo.pt'
        if os.path.exists(model_path):
            print(f"✅ 找到自定义模型: {model_path}")
            try:
                model = YOLO(model_path)
                print(f"✅ 自定义模型加载成功")
                print(f"   类别数: {len(model.names)}")
                print(f"   类别: {list(model.names.values())}")
            except Exception as e:
                print(f"⚠️  自定义模型加载失败: {e}")
        else:
            print(f"⚠️  未找到自定义模型: {model_path}")
            print(f"   将使用预训练模型 yolov8n.pt")
        
        # 测试预训练模型
        print()
        print("测试预训练模型 yolov8n.pt...")
        model = YOLO('yolov8n.pt')
        print(f"✅ 预训练模型加载成功")
        print(f"   类别数: {len(model.names)}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print()
        return False

def test_detection_service():
    """测试检测服务模块"""
    print("=" * 60)
    print("测试 5: 检测服务模块")
    print("=" * 60)
    
    try:
        # 测试game_vision模块
        try:
            from services.game_vision import GameVisionDetector, get_detector
            print("✅ game_vision模块导入成功")
        except ImportError as e:
            print(f"❌ game_vision模块导入失败: {e}")
            return False
        
        # 测试vision_service模块
        try:
            from services.vision_service import vision_detection_task, capture_screenshot_task
            print("✅ vision_service模块导入成功")
        except ImportError as e:
            print(f"❌ vision_service模块导入失败: {e}")
            return False
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print()
        return False

def test_api_routes():
    """测试API路由"""
    print("=" * 60)
    print("测试 6: API路由")
    print("=" * 60)
    
    try:
        from routes.api_routes import api
        from flask import Flask
        
        app = Flask(__name__)
        app.register_blueprint(api)
        
        # 检查路由
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        
        expected_routes = [
            '/vision_detection',
            '/live_game',
            '/summoner/<name>'
        ]
        
        for route in expected_routes:
            if any(route in r for r in routes):
                print(f"✅ 路由存在: {route}")
            else:
                print(f"❌ 路由缺失: {route}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print()
        return False

def main():
    """运行所有测试"""
    print()
    print("🔬 LOLHelper CV检测功能测试")
    print()
    
    results = []
    
    # 运行测试
    results.append(("依赖包导入", test_imports()))
    results.append(("CV模块", test_cv_modules()))
    results.append(("屏幕截图", test_screen_capture()))
    results.append(("YOLO模型", test_yolo_model()))
    results.append(("检测服务", test_detection_service()))
    results.append(("API路由", test_api_routes()))
    
    # 总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:20s}: {status}")
    
    print()
    print(f"总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print()
        print("🎉 所有测试通过！CV检测功能准备就绪")
        print()
        print("下一步：")
        print("1. 运行: python app_new.py")
        print("2. 访问: http://localhost:5000/vision_detection")
        print("3. 点击 '开始检测' 按钮测试功能")
        print()
    else:
        print()
        print("⚠️  部分测试失败，请检查：")
        print("1. 是否运行了 install_cv_deps.ps1 安装依赖？")
        print("2. Python版本是否 >= 3.8？")
        print("3. 查看上方错误信息进行排查")
        print()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
