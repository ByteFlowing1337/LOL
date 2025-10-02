"""
游戏画面数据收集工具
用于收集LOL游戏截图作为YOLO训练数据

使用方法:
1. 启动游戏
2. 运行此脚本: python tools/collect_training_data.py
3. 游戏中按 F12 截图
4. 截图自动保存到 training_data/images/
"""

import os
import time
import mss
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
import keyboard  # pip install keyboard


class TrainingDataCollector:
    """训练数据收集器"""
    
    def __init__(self, output_dir="training_data"):
        """
        初始化收集器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images" / "raw"
        
        # 创建目录
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        self.screenshot_count = 0
        self.last_screenshot_time = 0
        self.min_interval = 1.0  # 最小截图间隔（秒）
        
        print("=" * 60)
        print("🎮 LOL训练数据收集工具")
        print("=" * 60)
        print(f"📁 保存路径: {self.images_dir.absolute()}")
        print()
        print("📝 使用说明:")
        print("  1. 启动LOL游戏（训练模式或自定义对局）")
        print("  2. 按 F12 截取游戏画面")
        print("  3. 按 ESC 退出收集")
        print()
        print("💡 收集建议:")
        print("  - 收集不同英雄的画面（至少10个英雄）")
        print("  - 包含施法动作、技能指示器、小地图等")
        print("  - 包含对线期和团战不同场景")
        print("  - 建议收集100-200张图片")
        print()
        print("⏳ 等待按键...")
        print("=" * 60)
        
    def capture_screenshot(self):
        """截取游戏画面"""
        try:
            with mss.mss() as sct:
                # 获取主显示器
                monitor = sct.monitors[1]
                
                # 截图
                screenshot = sct.grab(monitor)
                
                # 转换为OpenCV格式
                img = np.array(screenshot)
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                
                # 生成文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                filename = f"lol_screenshot_{timestamp}.jpg"
                filepath = self.images_dir / filename
                
                # 保存图片
                cv2.imwrite(str(filepath), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                
                self.screenshot_count += 1
                
                print(f"✅ [{self.screenshot_count:3d}] 截图保存: {filename}")
                print(f"   分辨率: {img.shape[1]}x{img.shape[0]}")
                
                return True
                
        except Exception as e:
            print(f"❌ 截图失败: {e}")
            return False
    
    def on_screenshot_key(self):
        """F12键按下时的回调"""
        current_time = time.time()
        
        # 防止连击
        if current_time - self.last_screenshot_time < self.min_interval:
            return
        
        self.last_screenshot_time = current_time
        self.capture_screenshot()
    
    def run(self):
        """运行收集器"""
        # 注册热键
        keyboard.add_hotkey('f12', self.on_screenshot_key)
        
        try:
            # 等待用户按键
            keyboard.wait('esc')
            
        except KeyboardInterrupt:
            pass
        
        finally:
            # 清理
            keyboard.unhook_all()
            
            print()
            print("=" * 60)
            print("📊 收集统计")
            print("=" * 60)
            print(f"总截图数: {self.screenshot_count}")
            print(f"保存路径: {self.images_dir.absolute()}")
            print()
            
            if self.screenshot_count > 0:
                print("🎯 下一步:")
                print("  1. 使用Roboflow或LabelImg标注数据")
                print("  2. 标注8个类别（见models/README.md）")
                print("  3. 导出YOLO格式数据集")
                print("  4. 运行训练脚本: python tools/train_yolo_model.py")
                print()
                print("📚 标注教程:")
                print("  Roboflow: https://roboflow.com/")
                print("  LabelImg: https://github.com/heartexlabs/labelImg")
            else:
                print("⚠️ 未收集到任何截图")
            
            print()
            print("👋 感谢使用！")
            print("=" * 60)


def main():
    """主函数"""
    collector = TrainingDataCollector()
    collector.run()


if __name__ == '__main__':
    main()
