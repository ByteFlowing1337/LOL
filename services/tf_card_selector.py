"""
卡牌大师黄牌自动选择功能
检测W技能的黄牌并自动按键锁定
"""
import cv2
import numpy as np
import time
import mss
from pynput import keyboard
from pynput.keyboard import Key, Controller

class TwistedFateCardSelector:
    """卡牌大师黄牌自动选择器"""
    
    def __init__(self):
        """初始化选择器"""
        self.keyboard_controller = Controller()
        self.w_pressed = False
        self.w_press_time = 0
        self.is_enabled = False
        self.current_champion = None
        self.keyboard_listener = None
        
        # 黄牌颜色范围（HSV色彩空间）
        self.yellow_card_ranges = [
            {
                'lower': np.array([20, 100, 200]),  # 黄色下限
                'upper': np.array([35, 255, 255])   # 黄色上限
            }
        ]
        
        # W技能区域（相对坐标）
        # 卡牌大师W技能会在头顶显示
        self.card_detection_region = {
            'left': 0.40,    # 屏幕中央区域
            'top': 0.25,
            'right': 0.60,
            'bottom': 0.50
        }
        
        # 反应时间阈值
        self.max_reaction_time = 0.15  # 150毫秒内完成检测和按键
        
        print("✅ 卡牌大师黄牌选择器初始化完成")
        print("💡 功能: 检测到黄牌后自动按W锁定")
    
    def set_champion(self, champion_name):
        """
        设置当前英雄
        
        Args:
            champion_name: 英雄名称
        """
        self.current_champion = champion_name
        # 检查是否是卡牌大师
        if champion_name and ('twisted' in champion_name.lower() or 
                              'fate' in champion_name.lower() or
                              '卡牌' in champion_name):
            self.is_enabled = True
            self.start_keyboard_listener()
            print(f"✅ 检测到卡牌大师，黄牌自动选择已启用")
        else:
            self.is_enabled = False
            self.stop_keyboard_listener()
    
    def start_keyboard_listener(self):
        """启动键盘监听器"""
        if self.keyboard_listener is None:
            def on_press(key):
                try:
                    # 监听W键
                    if hasattr(key, 'char') and key.char in ['w', 'W']:
                        self.on_w_pressed()
                except AttributeError:
                    pass
            
            self.keyboard_listener = keyboard.Listener(on_press=on_press)
            self.keyboard_listener.start()
            print("🎮 键盘监听已启动 - 监听W键")
    
    def stop_keyboard_listener(self):
        """停止键盘监听器"""
        if self.keyboard_listener is not None:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
            print("⏹️ 键盘监听已停止")
    
    def on_w_pressed(self):
        """W键按下事件"""
        if not self.is_enabled:
            return
        
        # 避免重复触发
        if self.w_pressed and (time.time() - self.w_press_time) < 0.5:
            return
        
        self.w_pressed = True
        self.w_press_time = time.time()
        print("🎯 检测到W键按下，开始监控黄牌...")
        print("💡 提示: 将在检测到黄牌后自动按W锁定")
    
    def capture_card_region(self):
        """
        捕获卡牌区域的屏幕截图
        
        Returns:
            numpy.ndarray: 截图图像
        """
        with mss.mss() as sct:
            # 获取屏幕尺寸
            monitor = sct.monitors[1]
            width = monitor['width']
            height = monitor['height']
            
            # 计算检测区域
            region = {
                'left': int(width * self.card_detection_region['left']) + monitor['left'],
                'top': int(height * self.card_detection_region['top']) + monitor['top'],
                'width': int(width * (self.card_detection_region['right'] - 
                                     self.card_detection_region['left'])),
                'height': int(height * (self.card_detection_region['bottom'] - 
                                       self.card_detection_region['top']))
            }
            
            # 截图
            screenshot = sct.grab(region)
            img = np.array(screenshot)
            
            # 转换颜色空间 BGRA -> BGR
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            return img
    
    def detect_yellow_card(self, img):
        """
        检测图像中的黄牌
        
        Args:
            img: 输入图像
        
        Returns:
            tuple: (是否检测到, 黄色像素比例)
        """
        # 转换到HSV色彩空间
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # 创建黄色掩码
        mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for color_range in self.yellow_card_ranges:
            temp_mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])
            mask = cv2.bitwise_or(mask, temp_mask)
        
        # 形态学操作去噪
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # 计算黄色像素比例
        total_pixels = mask.shape[0] * mask.shape[1]
        yellow_pixels = np.sum(mask > 0)
        yellow_ratio = yellow_pixels / total_pixels
        
        # 检测阈值：黄色像素占比 > 3%
        detected = yellow_ratio > 0.03
        
        return detected, yellow_ratio
    
    def press_w_key(self):
        """自动按下W键锁定黄牌"""
        try:
            self.keyboard_controller.press('w')
            time.sleep(0.01)  # 短暂延迟
            self.keyboard_controller.release('w')
            print("✅ 已自动按W锁定黄牌！")
            return True
        except Exception as e:
            print(f"❌ 按键失败: {e}")
            return False
    
    def check_and_select_yellow_card(self):
        """
        检查并选择黄牌（主检测循环）
        
        Returns:
            dict: 检测结果
        """
        if not self.is_enabled:
            return {
                'enabled': False,
                'message': '功能未启用（非卡牌大师）',
                'champion': self.current_champion
            }
        
        if not self.w_pressed:
            return {
                'enabled': True,
                'w_pressed': False,
                'message': '等待W键按下',
                'champion': self.current_champion
            }
        
        # 检查是否超时
        elapsed_time = time.time() - self.w_press_time
        if elapsed_time > 3.0:  # W技能持续约3秒
            self.w_pressed = False
            print("⏱️ W技能持续时间结束")
            return {
                'enabled': True,
                'w_pressed': False,
                'message': 'W技能已结束',
                'timeout': True,
                'champion': self.current_champion
            }
        
        try:
            # 捕获屏幕
            img = self.capture_card_region()
            
            # 检测黄牌
            detected, yellow_ratio = self.detect_yellow_card(img)
            
            result = {
                'enabled': True,
                'w_pressed': True,
                'yellow_detected': detected,
                'yellow_ratio': float(yellow_ratio),
                'elapsed_time': float(elapsed_time),
                'auto_pressed': False,
                'champion': self.current_champion
            }
            
            # 如果检测到黄牌，自动按W
            if detected:
                print(f"🎯 检测到黄牌！黄色占比: {yellow_ratio*100:.1f}%")
                if self.press_w_key():
                    result['auto_pressed'] = True
                    result['message'] = f'✅ 检测到黄牌（{yellow_ratio*100:.1f}%），已自动锁定！'
                    print(result['message'])
                else:
                    result['message'] = '❌ 检测到黄牌但按键失败'
                    print(result['message'])
                
                # 重置状态
                self.w_pressed = False
            else:
                result['message'] = f'⏳ 监控中... 黄色: {yellow_ratio*100:.1f}% (已用时: {elapsed_time:.2f}s)'
            
            return result
            
        except Exception as e:
            print(f"❌ 黄牌检测异常: {e}")
            return {
                'enabled': True,
                'w_pressed': True,
                'error': str(e),
                'message': f'检测异常: {e}',
                'champion': self.current_champion
            }
    
    def save_debug_image(self, img, detected, yellow_ratio):
        """
        保存调试图像
        
        Args:
            img: 原始图像
            detected: 是否检测到黄牌
            yellow_ratio: 黄色像素比例
        """
        import os
        from datetime import datetime
        
        # 创建调试目录
        debug_dir = "debug_tf_cards"
        os.makedirs(debug_dir, exist_ok=True)
        
        # 转换到HSV并创建掩码
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for color_range in self.yellow_card_ranges:
            temp_mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])
            mask = cv2.bitwise_or(mask, temp_mask)
        
        # 创建可视化图像
        vis_img = img.copy()
        vis_img[mask > 0] = [0, 255, 255]  # 黄色高亮
        
        # 添加文字信息
        status = "DETECTED" if detected else "WAITING"
        color = (0, 255, 0) if detected else (0, 0, 255)
        cv2.putText(vis_img, f"Status: {status}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(vis_img, f"Yellow: {yellow_ratio*100:.1f}%", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # 保存图像
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{debug_dir}/tf_card_{status}_{timestamp}.png"
        cv2.imwrite(filename, vis_img)
        
        return filename


# 全局实例
_tf_selector = None


def get_tf_selector():
    """获取全局卡牌选择器实例"""
    global _tf_selector
    if _tf_selector is None:
        _tf_selector = TwistedFateCardSelector()
    return _tf_selector


if __name__ == '__main__':
    """测试卡牌选择器"""
    print("=" * 60)
    print("🎮 卡牌大师黄牌选择器测试")
    print("=" * 60)
    
    selector = TwistedFateCardSelector()
    
    # 模拟设置卡牌大师
    selector.set_champion("TwistedFate")
    
    # 模拟W键按下
    selector.on_w_pressed()
    
    # 测试检测
    print("\n开始测试检测（按Ctrl+C停止）...")
    try:
        while True:
            result = selector.check_and_select_yellow_card()
            print(f"检测结果: {result['message']}")
            
            if result.get('auto_pressed'):
                print("✅ 成功锁定黄牌！")
                break
            
            time.sleep(0.05)  # 50ms检测间隔
            
    except KeyboardInterrupt:
        print("\n测试结束")
