"""
游戏视觉检测服务
基于YOLO的游戏画面分析
"""
import cv2
import numpy as np
import mss
import time
from pathlib import Path
from datetime import datetime
import json


class GameVisionDetector:
    """游戏视觉检测器"""
    
    def __init__(self, model_path=None):
        """
        初始化检测器
        
        Args:
            model_path: YOLO模型路径，如果为None则使用默认路径
        """
        self.model_path = model_path or "models/lol_yolo.pt"
        self.model = None
        # 不在初始化时创建mss实例，在每次截图时创建（线程安全）
        self.detection_enabled = False
        self.last_detections = []
        
        # 检测区域配置（相对于屏幕分辨率）
        self.regions = {
            'minimap': {'x': 0, 'y': 0.75, 'width': 0.15, 'height': 0.25},  # 小地图区域
            'skills': {'x': 0.35, 'y': 0.85, 'width': 0.3, 'height': 0.15},  # 技能栏区域
            'champion': {'x': 0.3, 'y': 0.3, 'width': 0.4, 'height': 0.4}    # 英雄中心区域
        }
        
        # 检测类别
        self.detection_classes = {
            0: 'champion_casting',      # 英雄抬手/施法
            1: 'enemy_champion',        # 敌方英雄
            2: 'ally_champion',         # 友方英雄
            3: 'skillshot_indicator',   # 技能指示器
            4: 'danger_ping',           # 危险信号
            5: 'objective_spawn',       # 野怪刷新
            6: 'low_health',            # 低血量
            7: 'enemy_ward',            # 敌方眼位
        }
        
        self._load_model()
    
    def _load_model(self):
        """加载YOLO模型"""
        try:
            # 尝试加载YOLOv8模型
            from ultralytics import YOLO
            
            model_file = Path(self.model_path)
            if model_file.exists():
                self.model = YOLO(str(model_file))
                print(f"✅ YOLO模型加载成功: {self.model_path}")
            else:
                print(f"⚠️ 模型文件不存在: {self.model_path}")
                print("💡 提示: 请先训练或下载YOLO模型")
                print("    可以使用YOLOv8预训练模型: yolov8n.pt")
                # 尝试加载预训练模型
                try:
                    self.model = YOLO('yolov8n.pt')
                    print("✅ 使用YOLOv8预训练模型")
                except:
                    print("❌ 无法加载模型，检测功能将被禁用")
                    
        except ImportError:
            print("❌ ultralytics库未安装")
            print("💡 安装命令: pip install ultralytics")
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
    
    def capture_screen(self, region=None):
        """
        截取屏幕（线程安全版本）
        
        Args:
            region: 截取区域 {'x', 'y', 'width', 'height'}，None表示全屏
        
        Returns:
            numpy.ndarray: 截图图像
        """
        # 每次调用时创建新的mss实例（线程安全）
        with mss.mss() as sct:
            if region is None:
                # 获取主显示器
                monitor = sct.monitors[1]
            else:
                # 计算实际像素区域
                monitor_info = sct.monitors[1]
                screen_width = monitor_info['width']
                screen_height = monitor_info['height']
                
                monitor = {
                    'left': int(monitor_info['left'] + region['x'] * screen_width),
                    'top': int(monitor_info['top'] + region['y'] * screen_height),
                    'width': int(region['width'] * screen_width),
                    'height': int(region['height'] * screen_height)
                }
            
            # 截图
            screenshot = sct.grab(monitor)
            # 转换为OpenCV格式
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            return img
    
    def detect_objects(self, image, confidence_threshold=0.5):
        """
        在图像中检测对象
        
        Args:
            image: 输入图像
            confidence_threshold: 置信度阈值
        
        Returns:
            list: 检测结果列表
        """
        if self.model is None:
            return []
        
        try:
            # 使用YOLO进行检测
            results = self.model(image, conf=confidence_threshold, verbose=False)
            
            detections = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    detection = {
                        'class_id': int(box.cls[0]),
                        'class_name': self.detection_classes.get(int(box.cls[0]), 'unknown'),
                        'confidence': float(box.conf[0]),
                        'bbox': box.xyxy[0].tolist(),  # [x1, y1, x2, y2]
                        'timestamp': time.time()
                    }
                    detections.append(detection)
            
            return detections
            
        except Exception as e:
            print(f"检测错误: {e}")
            return []
    
    def detect_champion_casting(self):
        """
        检测英雄抬手/施法动作
        
        Returns:
            dict: 检测结果
        """
        # 截取英雄中心区域
        img = self.capture_screen(self.regions['champion'])
        detections = self.detect_objects(img, confidence_threshold=0.6)
        
        # 筛选抬手动作
        casting_detections = [d for d in detections if d['class_name'] == 'champion_casting']
        
        return {
            'detected': len(casting_detections) > 0,
            'count': len(casting_detections),
            'detections': casting_detections,
            'timestamp': datetime.now().isoformat()
        }
    
    def detect_minimap_enemies(self):
        """
        检测小地图中的敌方英雄
        
        Returns:
            dict: 检测结果
        """
        # 截取小地图区域
        img = self.capture_screen(self.regions['minimap'])
        detections = self.detect_objects(img, confidence_threshold=0.5)
        
        # 筛选敌方英雄
        enemy_detections = [d for d in detections if d['class_name'] == 'enemy_champion']
        
        return {
            'detected': len(enemy_detections) > 0,
            'enemy_count': len(enemy_detections),
            'positions': [(d['bbox'][0], d['bbox'][1]) for d in enemy_detections],
            'detections': enemy_detections,
            'timestamp': datetime.now().isoformat()
        }
    
    def detect_danger_signals(self):
        """
        检测危险信号（低血量、敌人靠近等）
        
        Returns:
            dict: 检测结果
        """
        img = self.capture_screen()
        detections = self.detect_objects(img, confidence_threshold=0.7)
        
        # 筛选危险信号
        danger_types = ['low_health', 'danger_ping', 'enemy_champion']
        danger_detections = [d for d in detections if d['class_name'] in danger_types]
        
        # 按类型分组
        grouped = {}
        for d in danger_detections:
            class_name = d['class_name']
            if class_name not in grouped:
                grouped[class_name] = []
            grouped[class_name].append(d)
        
        return {
            'has_danger': len(danger_detections) > 0,
            'danger_level': 'high' if len(danger_detections) >= 3 else 'medium' if len(danger_detections) > 0 else 'low',
            'detections_by_type': grouped,
            'total_detections': len(danger_detections),
            'timestamp': datetime.now().isoformat()
        }
    
    def detect_skill_indicators(self):
        """
        检测技能指示器
        
        Returns:
            dict: 检测结果
        """
        img = self.capture_screen(self.regions['skills'])
        detections = self.detect_objects(img, confidence_threshold=0.6)
        
        skill_detections = [d for d in detections if d['class_name'] == 'skillshot_indicator']
        
        return {
            'detected': len(skill_detections) > 0,
            'skill_count': len(skill_detections),
            'detections': skill_detections,
            'timestamp': datetime.now().isoformat()
        }
    
    def comprehensive_detection(self):
        """
        综合检测（所有功能）
        
        Returns:
            dict: 完整的检测结果
        """
        return {
            'casting': self.detect_champion_casting(),
            'minimap_enemies': self.detect_minimap_enemies(),
            'danger_signals': self.detect_danger_signals(),
            'skill_indicators': self.detect_skill_indicators(),
            'overall_timestamp': datetime.now().isoformat()
        }
    
    def save_detection_image(self, image, detections, save_dir='detections'):
        """
        保存带有检测框的图像
        
        Args:
            image: 原始图像
            detections: 检测结果列表
            save_dir: 保存目录
        """
        output_dir = Path(save_dir)
        output_dir.mkdir(exist_ok=True)
        
        # 绘制检测框
        img_with_boxes = image.copy()
        for det in detections:
            x1, y1, x2, y2 = [int(v) for v in det['bbox']]
            label = f"{det['class_name']} {det['confidence']:.2f}"
            
            # 绘制框
            cv2.rectangle(img_with_boxes, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # 绘制标签
            cv2.putText(img_with_boxes, label, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # 保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = output_dir / f"detection_{timestamp}.jpg"
        cv2.imwrite(str(filename), img_with_boxes)
        
        return str(filename)


# 全局检测器实例
_detector_instance = None

def get_detector():
    """获取全局检测器实例"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = GameVisionDetector()
    return _detector_instance
