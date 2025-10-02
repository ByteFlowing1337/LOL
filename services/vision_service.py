"""
CV检测后台任务
持续监控游戏画面并发送检测结果
支持三种检测模式：传统CV、YOLO、混合模式
包含卡牌大师黄牌自动选择功能
"""
import time
import threading
import numpy as np
from config import app_state
from services.game_vision import get_detector
from services.traditional_cv_detector import get_traditional_detector

# 导入卡牌大师黄牌选择器
try:
    from services.tf_card_selector import get_tf_selector
    TF_SELECTOR_AVAILABLE = True
except ImportError:
    TF_SELECTOR_AVAILABLE = False
    print("⚠️ 卡牌大师黄牌选择器不可用（缺少pynput库）")

# 导入英雄监控器
try:
    from services.champion_monitor import get_champion_monitor
    CHAMPION_MONITOR_AVAILABLE = True
except ImportError:
    CHAMPION_MONITOR_AVAILABLE = False
    print("⚠️ 英雄监控器不可用")

# 导入配置（如果配置文件存在）
try:
    from cv_detection_config import (
        USE_TRADITIONAL_CV,
        USE_YOLO,
        DETECTION_INTERVAL,
        YOLO_CONFIDENCE_THRESHOLD
    )
except ImportError:
    # 默认配置
    USE_TRADITIONAL_CV = True
    USE_YOLO = False  # 默认只用传统CV
    DETECTION_INTERVAL = 1.0
    YOLO_CONFIDENCE_THRESHOLD = 0.5

# 导入模式管理（如果存在）
try:
    from cv_mode_selector import CVDetectionMode
except ImportError:
    # 定义简单的模式枚举
    class CVDetectionMode:
        TRADITIONAL = "traditional"
        YOLO = "yolo"
        HYBRID = "hybrid"


def convert_to_json_serializable(obj):
    """
    将对象转换为JSON可序列化的格式
    处理NumPy类型、布尔值等
    
    Args:
        obj: 要转换的对象
    
    Returns:
        JSON可序列化的对象
    """
    if isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, np.str_):
        return str(obj)
    else:
        return obj


def vision_detection_task(socketio, detection_interval=None, mode=None):
    """
    视觉检测后台任务（支持三种模式）
    
    Args:
        socketio: Flask-SocketIO实例
        detection_interval: 检测间隔（秒），None则使用配置文件
        mode: 检测模式 ('traditional', 'yolo', 'hybrid')，None则根据配置判断
    """
    # 使用参数或配置文件
    interval = detection_interval if detection_interval is not None else DETECTION_INTERVAL
    
    # 确定检测模式
    if mode is None:
        # 根据配置判断模式
        if USE_TRADITIONAL_CV and USE_YOLO:
            mode = CVDetectionMode.HYBRID
        elif USE_TRADITIONAL_CV:
            mode = CVDetectionMode.TRADITIONAL
        elif USE_YOLO:
            mode = CVDetectionMode.YOLO
        else:
            print("❌ 错误: 至少需要启用一种检测模式！")
            return
    
    # 初始化检测器
    if mode in [CVDetectionMode.TRADITIONAL, CVDetectionMode.HYBRID, "traditional", "hybrid"]:
        traditional_detector = get_traditional_detector()
        mode_name = "传统CV模式"
    else:
        traditional_detector = None
    
    if mode in [CVDetectionMode.YOLO, CVDetectionMode.HYBRID, "yolo", "hybrid"]:
        yolo_detector = get_detector()
        mode_name = "YOLO深度学习模式"
    else:
        yolo_detector = None
    
    # 初始化卡牌大师选择器
    tf_selector = None
    if TF_SELECTOR_AVAILABLE:
        tf_selector = get_tf_selector()
        print("🃏 卡牌大师黄牌自动选择已启用")
    
    # 初始化英雄监控器
    champion_monitor = None
    if CHAMPION_MONITOR_AVAILABLE and TF_SELECTOR_AVAILABLE:
        champion_monitor = get_champion_monitor()
        champion_monitor.set_tf_selector(tf_selector)
        
        # 添加英雄改变回调
        def on_champion_change(champion_name, champion_id):
            """当英雄改变时的回调"""
            from config import socketio
            socketio.emit('champion_changed', {
                'champion': champion_name,
                'championId': champion_id,
                'tfEnabled': champion_name == 'TwistedFate'
            })
        
        champion_monitor.add_champion_change_callback(on_champion_change)
        champion_monitor.start_monitoring()
        print("👀 英雄自动监控已启用")
    
    # 确定模式名称
    if mode in [CVDetectionMode.HYBRID, "hybrid"]:
        mode_name = "混合模式 (传统CV + YOLO)"
    elif mode in [CVDetectionMode.TRADITIONAL, "traditional"]:
        mode_name = "传统CV模式 (OpenCV)"
    elif mode in [CVDetectionMode.YOLO, "yolo"]:
        mode_name = "YOLO深度学习模式"
    
    print(f"\n{'=' * 60}")
    print(f"🎥 CV检测服务已启动")
    print(f"📋 检测模式: {mode_name}")
    print(f"⏱️  检测间隔: {interval}秒")
    if mode in [CVDetectionMode.TRADITIONAL, "traditional"]:
        print(f"✅ 特点: 速度快、无需模型、立即可用")
        print(f"� 检测内容: 小地图(右下角)、血量、技能CD、危险信号")
    elif mode in [CVDetectionMode.YOLO, "yolo"]:
        print(f"✅ 特点: 高精度、需要模型、深度学习")
        print(f"🎯 检测内容: 英雄动作、技能指示器、复杂场景")
    else:
        print(f"✅ 特点: 性能均衡、准确度高、推荐使用")
        print(f"🎯 检测内容: 全面检测(UI + 动作)")
    print(f"{'=' * 60}\n")
    
    # 不自动启动卡牌辅助，等待用户手动启用
    # 卡牌辅助需要用户在前端点击按钮后，通过socket事件启动
    
    while True:
        if app_state.vision_detection_enabled:
            try:
                # 根据模式选择检测方法
                if mode in [CVDetectionMode.HYBRID, "hybrid"]:
                    # 混合模式
                    results = _hybrid_detection(traditional_detector, yolo_detector)
                elif mode in [CVDetectionMode.TRADITIONAL, "traditional"]:
                    # 仅传统CV
                    results = traditional_detector.comprehensive_detection()
                    # 格式化为统一格式
                    results = _format_traditional_results(results)
                else:
                    # 仅YOLO
                    results = yolo_detector.comprehensive_detection()
                
                # 转换为JSON可序列化格式
                serializable_results = convert_to_json_serializable(results)
                
                # 添加卡牌大师状态到结果中
                if tf_selector:
                    serializable_results['tf_card_selector'] = {
                        'enabled': tf_selector.is_enabled,
                        'champion': tf_selector.current_champion,
                        'w_pressed': tf_selector.w_pressed,
                        'w_press_time': tf_selector.w_press_time if tf_selector.w_pressed else 0
                    }
                
                # 发送检测结果到前端
                socketio.emit('vision_detection_update', {
                    'success': True,
                    'data': serializable_results,
                    'mode': mode_name
                })
                
                # 处理特定事件
                _handle_detection_events(results, socketio)
                
            except Exception as e:
                print(f"❌ CV检测任务异常: {e}")
                import traceback
                traceback.print_exc()
                socketio.emit('vision_detection_update', {
                    'success': False,
                    'error': str(e)
                })
            
            time.sleep(interval)
        else:
            time.sleep(2)


def _hybrid_detection(traditional_detector, yolo_detector):
    """
    混合检测：传统CV + YOLO
    
    策略：
    - 传统CV检测固定UI元素（快速、准确）
    - YOLO检测动态内容（准确、全面）
    
    Args:
        traditional_detector: 传统CV检测器
        yolo_detector: YOLO检测器
    
    Returns:
        dict: 综合检测结果
    """
    start_time = time.time()
    
    # 1. 传统CV检测（优先，快速）
    traditional_results = traditional_detector.comprehensive_detection()
    
    # 2. YOLO检测（仅检测复杂目标）
    yolo_results = {
        'casting': {'detected': False, 'detections': []},
        'skill_indicators': {'detected': False, 'detections': []}
    }
    
    # 如果YOLO模型可用，检测英雄抬手和技能指示器
    if yolo_detector.model:
        try:
            screen = yolo_detector.capture_screen()
            detections = yolo_detector.detect_objects(screen, confidence_threshold=0.5)
            
            # 过滤结果
            casting_detections = [d for d in detections if d['class_name'] == 'champion_casting']
            skill_detections = [d for d in detections if d['class_name'] == 'skillshot_indicator']
            
            yolo_results['casting'] = {
                'detected': bool(len(casting_detections) > 0),
                'detections': casting_detections,
                'count': int(len(casting_detections))
            }
            
            yolo_results['skill_indicators'] = {
                'detected': bool(len(skill_detections) > 0),
                'detections': skill_detections,
                'count': int(len(skill_detections))
            }
        except:
            pass  # YOLO失败时继续使用传统CV结果
    
    # 3. 整合结果
    results = {
        'timestamp': float(traditional_results['timestamp']),
        
        # 来自传统CV的结果
        'minimap_enemies': {
            'detected': bool(len(traditional_results['minimap_enemies']) > 0),
            'enemy_count': int(len(traditional_results['minimap_enemies'])),
            'enemies': traditional_results['minimap_enemies'],
            'method': 'traditional_cv'
        },
        
        'health_status': {
            'is_low': bool(traditional_results['health_status']['is_low']),
            'health_percent': float(traditional_results['health_status']['health_percent']),
            'severity': str(traditional_results['health_status']['severity']),
            'method': 'traditional_cv'
        },
        
        'danger_signals': {
            'detected': bool(len(traditional_results['danger_signals']) > 0),
            'signals': traditional_results['danger_signals'],
            'count': int(len(traditional_results['danger_signals'])),
            'method': 'traditional_cv'
        },
        
        'skill_status': {
            'skills': traditional_results['skill_status'],
            'cd_count': int(sum(1 for s in traditional_results['skill_status'] if s['on_cooldown'])),
            'method': 'traditional_cv'
        },
        
        # 来自YOLO的结果
        'casting': yolo_results['casting'],
        'skill_indicators': yolo_results['skill_indicators'],
        
        # 性能统计
        'detection_time': float(time.time() - start_time)
    }
    
    return results


def _format_traditional_results(traditional_results):
    """
    将传统CV结果格式化为统一格式
    
    Args:
        traditional_results: 传统CV检测器的原始结果
    
    Returns:
        dict: 格式化后的结果
    """
    return {
        'timestamp': float(traditional_results['timestamp']),
        
        'minimap_enemies': {
            'detected': bool(len(traditional_results['minimap_enemies']) > 0),
            'enemy_count': int(len(traditional_results['minimap_enemies'])),
            'enemies': traditional_results['minimap_enemies'],
            'method': 'traditional_cv'
        },
        
        'health_status': {
            'is_low': bool(traditional_results['health_status']['is_low']),
            'health_percent': float(traditional_results['health_status']['health_percent']),
            'severity': str(traditional_results['health_status']['severity']),
            'method': 'traditional_cv'
        },
        
        'danger_signals': {
            'detected': bool(len(traditional_results['danger_signals']) > 0),
            'signals': traditional_results['danger_signals'],
            'count': int(len(traditional_results['danger_signals'])),
            'method': 'traditional_cv'
        },
        
        'skill_status': {
            'skills': traditional_results['skill_status'],
            'cd_count': int(sum(1 for s in traditional_results['skill_status'] if s['on_cooldown'])),
            'method': 'traditional_cv'
        },
        
        # 传统CV不提供这些检测
        'casting': {'detected': False, 'detections': []},
        'skill_indicators': {'detected': False, 'detections': []},
        
        'detection_time': 0.0  # 会在外部计算
    }


def _handle_detection_events(results, socketio):
    """
    处理检测事件，触发相应的警报
    
    Args:
        results: 检测结果（混合格式）
        socketio: SocketIO实例
    """
    # 英雄抬手警报（YOLO检测）
    if results.get('casting', {}).get('detected', False):
        count = results['casting'].get('count', 0)
        socketio.emit('alert', {
            'type': 'champion_casting',
            'message': f'⚠️ 检测到 {count} 个英雄施法动作！',
            'severity': 'medium',
            'data': results['casting']
        })
    
    # 小地图敌人警报（传统CV检测）
    if results.get('minimap_enemies', {}).get('detected', False):
        enemy_count = results['minimap_enemies']['enemy_count']
        socketio.emit('alert', {
            'type': 'minimap_enemies',
            'message': f'🚨 小地图发现 {enemy_count} 个敌人！',
            'severity': 'high',
            'data': results['minimap_enemies']
        })
    
    # 低血量警报（传统CV检测）
    if results.get('health_status', {}).get('is_low', False):
        health_percent = results['health_status']['health_percent'] * 100
        severity = results['health_status']['severity']
        socketio.emit('alert', {
            'type': 'low_health',
            'message': f'💔 低血量警告！当前血量: {health_percent:.0f}%',
            'severity': severity,
            'data': results['health_status']
        })
    
    # 危险信号警报（传统CV检测）
    if results.get('danger_signals', {}).get('detected', False):
        count = results['danger_signals']['count']
        socketio.emit('alert', {
            'type': 'danger_signals',
            'message': f'⚠️ 发现 {count} 个危险信号！',
            'severity': 'medium',
            'data': results['danger_signals']
        })
    
    # 技能指示器警报（YOLO检测）
    if results.get('skill_indicators', {}).get('detected', False):
        count = results['skill_indicators'].get('count', 0)
        socketio.emit('alert', {
            'type': 'skill_indicators',
            'message': f'⚡ 检测到 {count} 个技能指示器！',
            'severity': 'low',
            'data': results['skill_indicators']
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


def _tf_card_detection_loop(tf_selector, socketio):
    """
    卡牌大师黄牌检测高频循环（独立线程）
    以50ms间隔持续检测黄牌，确保秒切反应
    
    Args:
        tf_selector: 卡牌选择器实例
        socketio: SocketIO实例
    """
    print("🃏 卡牌大师黄牌检测线程启动")
    last_w_pressed_state = False
    
    while True:
        try:
            # 检查CV检测和英雄监控是否都在运行
            from services.champion_monitor import get_champion_monitor
            champion_monitor = get_champion_monitor()
            
            if app_state.vision_detection_enabled and champion_monitor.is_monitoring:
                # 执行黄牌检测
                tf_result = tf_selector.check_and_select_yellow_card()
                
                # W键状态改变时通知前端
                current_w_pressed = tf_result.get('w_pressed', False)
                if current_w_pressed != last_w_pressed_state:
                    last_w_pressed_state = current_w_pressed
                    if current_w_pressed:
                        socketio.emit('tf_w_key_pressed', {
                            'message': '🎯 W键已按下，开始监控黄牌...'
                        })
                
                # 黄牌锁定成功时通知前端
                if tf_result.get('auto_pressed'):
                    socketio.emit('tf_yellow_card_locked', {
                        'success': True,
                        'message': tf_result.get('message', '✅ 黄牌已锁定'),
                        'yellow_ratio': tf_result.get('yellow_ratio', 0),
                        'elapsed_time': tf_result.get('elapsed_time', 0)
                    })
                    print(f"🎉 {tf_result.get('message')}")
                
                # 高频检测：50ms间隔（确保快速反应）
                time.sleep(0.05)
            else:
                # 功能未启用时降低检测频率
                time.sleep(0.5)
                
        except Exception as e:
            print(f"❌ 卡牌检测线程异常: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(1)  # 发生异常时等待1秒
