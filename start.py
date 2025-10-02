"""
LOLHelper 快速启动脚本
自动检查环境并启动应用
"""
import sys
import os
import subprocess

def check_dependencies():
    """检查必要的依赖"""
    print("🔍 检查依赖...")
    
    required_packages = [
        'flask',
        'flask_socketio',
        'opencv-python',
        'numpy',
        'mss',
        'ultralytics'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (缺失)")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️ 缺少依赖: {', '.join(missing)}")
        print("\n安装命令:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    print("✅ 所有依赖已安装\n")
    return True


def check_models():
    """检查模型文件"""
    print("🔍 检查模型文件...")
    
    model_path = "models/lol_yolo.pt"
    if os.path.exists(model_path):
        print(f"  ✅ YOLO模型: {model_path}")
        return True
    else:
        print(f"  ⚠️ YOLO模型未找到: {model_path}")
        print("  💡 应用将在 '传统CV模式' 下运行（无需模型）\n")
        return False


def check_config():
    """检查配置文件"""
    print("🔍 检查配置...")
    
    config_file = "cv_detection_config.py"
    if os.path.exists(config_file):
        print(f"  ✅ 配置文件: {config_file}")
        
        # 验证配置
        try:
            from cv_detection_config import validate_config
            if validate_config():
                from cv_detection_config import print_config_summary
                print_config_summary()
            else:
                print("  ⚠️ 配置文件存在错误，请检查")
                return False
        except Exception as e:
            print(f"  ⚠️ 配置加载失败: {e}")
            return False
    else:
        print(f"  ⚠️ 配置文件未找到: {config_file}")
        print("  💡 将使用默认配置\n")
    
    return True


def run_tests():
    """运行快速测试"""
    print("🧪 运行快速测试...")
    
    try:
        result = subprocess.run(
            [sys.executable, "test_hybrid_mode.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("  ✅ 测试通过")
            return True
        else:
            print("  ❌ 测试失败")
            print(result.stdout)
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("  ⚠️ 测试超时")
        return False
    except Exception as e:
        print(f"  ⚠️ 测试异常: {e}")
        return False


def start_app():
    """启动应用"""
    print("\n" + "=" * 60)
    print("🚀 启动 LOLHelper WebUI")
    print("=" * 60)
    
    try:
        # 使用 subprocess 启动应用
        subprocess.run([sys.executable, "app_new.py"])
    except KeyboardInterrupt:
        print("\n\n⚠️ 应用已停止")
    except Exception as e:
        print(f"\n\n❌ 启动失败: {e}")
        sys.exit(1)


def main():
    """主函数"""
    print("=" * 60)
    print("🎮 LOLHelper WebUI - 启动向导")
    print("=" * 60)
    print()
    
    # 1. 检查依赖
    if not check_dependencies():
        print("\n❌ 请先安装缺失的依赖")
        input("\n按回车键退出...")
        sys.exit(1)
    
    # 2. 检查模型
    has_model = check_models()
    
    # 3. 检查配置
    if not check_config():
        print("\n⚠️ 配置存在问题，但仍可继续运行")
    
    # 4. 询问是否运行测试
    print("\n" + "-" * 60)
    response = input("是否运行快速测试？(y/N): ").strip().lower()
    if response in ['y', 'yes']:
        if not run_tests():
            print("\n⚠️ 测试未通过，是否继续启动应用？")
            response = input("继续？(y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                sys.exit(1)
    
    # 5. 启动应用
    print("\n💡 应用启动后，请访问:")
    print("   主页: http://localhost:5000")
    print("   CV检测: http://localhost:5000/vision_detection")
    print("\n按 Ctrl+C 停止应用\n")
    
    input("按回车键启动应用...")
    start_app()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 启动已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")
        sys.exit(1)
