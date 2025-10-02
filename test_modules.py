"""
测试脚本 - 验证模块导入
"""

def test_imports():
    """测试所有模块是否可以正常导入"""
    print("开始测试模块导入...")
    
    try:
        print("✓ 导入 config")
        import config
        
        print("✓ 导入 routes")
        from routes import api_bp
        
        print("✓ 导入 services")
        from services import auto_accept_task, auto_analyze_task
        
        print("✓ 导入 utils")
        from utils import get_local_ip
        
        print("✓ 导入 websocket")
        from websocket import register_socket_events
        
        print("\n✅ 所有模块导入成功!")
        print("\n状态检查:")
        print(f"  - AppState 实例: {config.app_state}")
        print(f"  - LCU连接状态: {config.app_state.is_lcu_connected()}")
        print(f"  - 本地IP: {get_local_ip()}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_imports()
    if success:
        print("\n🎉 模块化结构验证通过，可以运行 app_new.py")
    else:
        print("\n⚠️ 存在问题，请检查错误信息")
