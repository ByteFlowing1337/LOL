"""
CV检测后台任务
持续监控游戏画面并发送检测结果
"""
import time
import threading
from config import app_state
from services.game_vision import get_detector


def vision_detection_task(socketio, detection_interval=1.0):
    """
    视觉检测后台任务
    
    Args:
        socketio: Flask-SocketIO实例
        detection_interval: 检测间隔（秒）
    """
    detector = get_detector()
    
    print("🎥 CV检测服务已启动")
    
    while True:
        if app_state.vision_detection_enabled:
            try:
                # 执行综合检测
                results = detector.comprehensive_detection()
                
                # 发送检测结果到前端
                socketio.emit('vision_detection_update', {
                    'success': True,
                    'data': results
                })
                
                # 处理特定事件
                _handle_detection_events(results, socketio)
                
            except Exception as e:
                print(f"❌ CV检测任务异常: {e}")
                socketio.emit('vision_detection_update', {
                    'success': False,
                    'error': str(e)
                })
            
            time.sleep(detection_interval)
        else:
            time.sleep(2)


def _handle_detection_events(results, socketio):
    """
    处理检测事件，触发相应的警报
    
    Args:
        results: 检测结果
        socketio: SocketIO实例
    """
    # 英雄抬手警报
    if results['casting']['detected']:
        socketio.emit('alert', {
            'type': 'champion_casting',
            'message': '⚠️ 检测到英雄施法动作！',
            'severity': 'medium',
            'data': results['casting']
        })
    
    # 小地图敌人警报
    if results['minimap_enemies']['detected']:
        enemy_count = results['minimap_enemies']['enemy_count']
        socketio.emit('alert', {
            'type': 'minimap_enemies',
            'message': f'🚨 小地图发现 {enemy_count} 个敌人！',
            'severity': 'high',
            'data': results['minimap_enemies']
        })
    
    # 危险信号警报
    danger_level = results['danger_signals']['danger_level']
    if danger_level in ['medium', 'high']:
        socketio.emit('alert', {
            'type': 'danger',
            'message': f'⚠️ 危险等级: {danger_level.upper()}',
            'severity': danger_level,
            'data': results['danger_signals']
        })


def capture_screenshot_task(socketio, save_detections=True):
    """
    截图任务（按需触发）
    
    Args:
        socketio: SocketIO实例
        save_detections: 是否保存检测结果
    """
    try:
        detector = get_detector()
        
        # 全屏截图
        img = detector.capture_screen()
        
        # 执行检测
        detections = detector.detect_objects(img)
        
        # 保存图像
        if save_detections and detections:
            saved_path = detector.save_detection_image(img, detections)
            socketio.emit('screenshot_saved', {
                'success': True,
                'path': saved_path,
                'detections_count': len(detections)
            })
            print(f"📸 截图已保存: {saved_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 截图失败: {e}")
        socketio.emit('screenshot_saved', {
            'success': False,
            'error': str(e)
        })
        return False
