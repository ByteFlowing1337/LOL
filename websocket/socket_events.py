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
    def handle_start_vision_detection():
        """启动CV视觉检测"""
        with thread_lock:
            if app_state.vision_detection_thread is None or not app_state.vision_detection_thread.is_alive():
                app_state.vision_detection_enabled = True
                app_state.vision_detection_thread = threading.Thread(
                    target=vision_detection_task,
                    args=(socketio,),
                    daemon=True
                )
                app_state.vision_detection_thread.start()
                emit('status_update', {'message': '✅ CV视觉检测已开启'})
                print("🎥 CV视觉检测功能已启动")
            else:
                emit('status_update', {'message': '⚠️ CV检测已在运行中'})
    
    @socketio.on('stop_vision_detection')
    def handle_stop_vision_detection():
        """停止CV视觉检测"""
        app_state.vision_detection_enabled = False
        emit('status_update', {'message': '⏸️ CV视觉检测已停止'})
        print("🎥 CV视觉检测已停止")
    
    @socketio.on('capture_screenshot')
    def handle_capture_screenshot():
        """手动截图"""
        print("📸 收到截图请求")
        socketio.start_background_task(capture_screenshot_task, socketio)


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
