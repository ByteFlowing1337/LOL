"""
WebSocket事件处理模块
"""
import threading
from flask_socketio import emit
from config import app_state
from services import auto_accept_task, auto_analyze_task
from services.vision_service import vision_detection_task, capture_screenshot_task
import lcu_api


class SocketIOMessageProxy:
    """用 Socket.IO 消息模拟 status_bar 的 showMessage 方法"""
    
    def __init__(self, socketio):
        self.socketio = socketio
    
    def showMessage(self, message):
        """发送状态消息到前端"""
        self.socketio.emit('status_update', {'data': message})
        print(f"[LCU连接] {message}")


def register_socket_events(socketio):
    """
    注册所有WebSocket事件处理器
    
    Args:
        socketio: Flask-SocketIO实例
    """
    thread_lock = threading.Lock()
    
    @socketio.on('connect')
    def handle_connect():
        """客户端连接事件"""
        print('浏览器客户端已连接，触发自动检测...')
        status_proxy = SocketIOMessageProxy(socketio)
        status_proxy.showMessage('已连接到本地服务器，开始自动检测LCU...')
        
        socketio.start_background_task(_detect_and_connect_lcu, socketio, status_proxy)
    
    @socketio.on('start_auto_accept')
    def handle_start_auto_accept():
        """启动自动接受对局"""
        with thread_lock:
            if app_state.auto_accept_thread is None or not app_state.auto_accept_thread.is_alive():
                app_state.auto_accept_enabled = True
                app_state.auto_accept_thread = threading.Thread(
                    target=auto_accept_task, 
                    args=(socketio,), 
                    daemon=True
                )
                app_state.auto_accept_thread.start()
                emit('status_update', {'message': '✅ 自动接受对局功能已开启'})
                print("🎮 自动接受对局功能已启动")
            else:
                emit('status_update', {'message': '⚠️ 自动接受功能已在运行中'})
    
    @socketio.on('start_auto_analyze')
    def handle_start_auto_analyze():
        """启动敌我分析"""
        with thread_lock:
            if app_state.auto_analyze_thread is None or not app_state.auto_analyze_thread.is_alive():
                app_state.auto_analyze_enabled = True
                app_state.auto_analyze_thread = threading.Thread(
                    target=auto_analyze_task, 
                    args=(socketio,), 
                    daemon=True
                )
                app_state.auto_analyze_thread.start()
                emit('status_update', {'message': '✅ 敌我分析功能已开启'})
                print("🔍 敌我分析功能已启动")
            else:
                emit('status_update', {'message': '⚠️ 敌我分析功能已在运行中'})
    
    @socketio.on('start_vision_detection')
    def handle_start_vision_detection(data=None):
        """
        启动CV视觉检测
        
        Args:
            data: 包含mode参数的字典 {'mode': 'traditional'/'yolo'/'hybrid'}
        """
        with thread_lock:
            if app_state.vision_detection_thread is None or not app_state.vision_detection_thread.is_alive():
                app_state.vision_detection_enabled = True
                
                # 从data中获取mode，默认为traditional
                mode = 'traditional'
                if data and isinstance(data, dict):
                    mode = data.get('mode', 'traditional')
                
                # 确定模式名称和描述
                mode_info = {
                    'traditional': {
                        'name': '传统CV模式',
                        'icon': '⚡',
                        'desc': '基于OpenCV，检测小地图(右下角)、血量、技能CD'
                    },
                    'yolo': {
                        'name': 'YOLO深度学习模式',
                        'icon': '🎯',
                        'desc': '基于YOLO模型，检测英雄动作、技能指示器'
                    },
                    'hybrid': {
                        'name': '混合模式',
                        'icon': '🚀',
                        'desc': '结合传统CV和YOLO优势'
                    }
                }
                
                info = mode_info.get(mode, mode_info['traditional'])
                
                app_state.vision_detection_thread = threading.Thread(
                    target=vision_detection_task,
                    args=(socketio,),
                    kwargs={'mode': mode},  # 传递模式参数
                    daemon=True
                )
                app_state.vision_detection_thread.start()
                
                message = f'{info["icon"]} CV视觉检测已开启 ({info["name"]})'
                emit('status_update', {'message': message})
                print(f"\n{'=' * 60}")
                print(f"🎥 CV视觉检测功能已启动")
                print(f"📋 模式: {info['name']}")
                print(f"📝 说明: {info['desc']}")
                print(f"{'=' * 60}\n")
            else:
                emit('status_update', {'message': '⚠️ CV检测已在运行中'})
    
    @socketio.on('stop_vision_detection')
    def handle_stop_vision_detection():
        """停止CV视觉检测"""
        app_state.vision_detection_enabled = False
        
        # 停止卡牌辅助
        try:
            from services.tf_card_selector import get_tf_selector
            selector = get_tf_selector()
            if selector.is_enabled:
                selector.stop_keyboard_listener()
                selector.is_enabled = False
                print("🃏 卡牌辅助已停止")
        except Exception as e:
            print(f"⚠️ 停止卡牌辅助时出错: {e}")
        
        # 停止英雄监控
        try:
            from services.champion_monitor import get_champion_monitor
            champion_monitor = get_champion_monitor()
            if champion_monitor.is_monitoring:
                champion_monitor.stop_monitoring()
                print("👀 英雄监控已停止")
        except Exception as e:
            print(f"⚠️ 停止英雄监控时出错: {e}")
        
        emit('status_update', {'message': '⏸️ CV视觉检测已停止'})
        print("🎥 CV视觉检测已停止")
    
    @socketio.on('start_tf_assist')
    def handle_start_tf_assist():
        """启动卡牌大师黄牌辅助"""
        with thread_lock:
            try:
                from services.tf_card_selector import get_tf_selector
                from services.champion_monitor import get_champion_monitor
                from services.vision_service import _tf_card_detection_loop
                
                # 检查CV检测是否运行
                if not app_state.vision_detection_enabled:
                    emit('status_update', {'message': '⚠️ 请先启动CV检测'})
                    return
                
                # 获取卡牌选择器
                selector = get_tf_selector()
                
                # 启动英雄监控
                champion_monitor = get_champion_monitor()
                champion_monitor.set_tf_selector(selector)
                
                # 添加英雄改变回调
                def on_champion_change(champion_name, champion_id, opgg_data=None):
                    data = {
                        'champion': champion_name,
                        'championId': champion_id,
                        'tfEnabled': champion_name == 'TwistedFate'
                    }
                    
                    # 添加OP.GG数据
                    if opgg_data:
                        data['opgg'] = opgg_data
                    
                    socketio.emit('champion_changed', data)
                
                champion_monitor.add_champion_change_callback(on_champion_change)
                champion_monitor.start_monitoring()
                
                # 启动卡牌检测线程
                if not hasattr(app_state, 'tf_detection_thread') or \
                   app_state.tf_detection_thread is None or \
                   not app_state.tf_detection_thread.is_alive():
                    app_state.tf_detection_thread = threading.Thread(
                        target=_tf_card_detection_loop,
                        args=(selector, socketio),
                        daemon=True
                    )
                    app_state.tf_detection_thread.start()
                    print("🃏 卡牌大师高频检测线程已启动（50ms间隔）")
                
                emit('status_update', {'message': '🃏 卡牌大师黄牌辅助已启用'})
                print("🃏 卡牌大师黄牌辅助已启用")
                print("👀 英雄自动监控已启动")
                
            except Exception as e:
                emit('status_update', {'message': f'❌ 启动卡牌辅助失败: {e}'})
                print(f"❌ 启动卡牌辅助失败: {e}")
                import traceback
                traceback.print_exc()
    
    @socketio.on('stop_tf_assist')
    def handle_stop_tf_assist():
        """停止卡牌大师黄牌辅助"""
        try:
            from services.tf_card_selector import get_tf_selector
            from services.champion_monitor import get_champion_monitor
            
            # 停止选择器
            selector = get_tf_selector()
            selector.stop_keyboard_listener()
            selector.is_enabled = False
            selector.current_champion = None
            
            # 停止监控
            champion_monitor = get_champion_monitor()
            if champion_monitor.is_monitoring:
                champion_monitor.stop_monitoring()
            
            emit('status_update', {'message': '🃏 卡牌大师黄牌辅助已停用'})
            print("🃏 卡牌大师黄牌辅助已停用")
            
        except Exception as e:
            emit('status_update', {'message': f'❌ 停止卡牌辅助失败: {e}'})
            print(f"❌ 停止卡牌辅助失败: {e}")
    
    @socketio.on('capture_screenshot')
    def handle_capture_screenshot():
        """手动截图"""
        print("📸 收到截图请求")
        socketio.start_background_task(capture_screenshot_task, socketio)
    
    @socketio.on('tf_set_champion')
    def handle_tf_set_champion(data):
        """
        设置当前英雄（用于卡牌大师检测）
        
        Args:
            data: {'champion': 'TwistedFate'}
        """
        try:
            from services.tf_card_selector import get_tf_selector
            champion = data.get('champion', '')
            selector = get_tf_selector()
            selector.set_champion(champion)
            emit('status_update', {'message': f'🃏 已设置英雄: {champion}'})
            print(f"🃏 卡牌大师选择器: 英雄设置为 {champion}")
        except Exception as e:
            print(f"❌ 设置英雄失败: {e}")
    
    @socketio.on('tf_w_pressed')
    def handle_tf_w_pressed():
        """W键按下事件"""
        try:
            from services.tf_card_selector import get_tf_selector
            selector = get_tf_selector()
            selector.on_w_pressed()
            emit('status_update', {'message': '🎯 W键按下，监控黄牌中...'})
            print("🎯 卡牌大师选择器: W键已按下")
        except Exception as e:
            print(f"❌ W键事件处理失败: {e}")


def _detect_and_connect_lcu(socketio, status_proxy):
    """
    后台任务：尝试获取 LCU 凭证
    
    Args:
        socketio: SocketIO实例
        status_proxy: 消息代理对象
    """
    status_proxy.showMessage("正在自动检测英雄联盟客户端 (进程和凭证)...")
    
    token, port = lcu_api.autodetect_credentials(status_proxy)

    if token and port:
        app_state.lcu_credentials["auth_token"] = token
        app_state.lcu_credentials["app_port"] = port
        status_proxy.showMessage(f"✅ LCU 连接成功！端口: {port}。")
    else:
        app_state.lcu_credentials["auth_token"] = None
        app_state.lcu_credentials["app_port"] = None
        status_proxy.showMessage("❌ 连接 LCU 失败。请检查客户端是否运行或重启程序。")
