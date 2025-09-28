# main.py

import sys
import os
import ctypes
import tempfile
import requests

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# 导入主窗口类和样式
from ui import LOLMatchHistoryApp
from styles import MAIN_STYLE_SHEET


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 应用样式
    app.setStyleSheet(MAIN_STYLE_SHEET)
    
        
        # 设置Windows任务栏图标
    if os.name == 'nt':
            myappid = 'ByteFlowing.LOLMatchHistory.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    # 创建主窗口实例
    window = LOLMatchHistoryApp()
    # 自动检测连接
    window.autodetect_params()
    
    window.show()
    sys.exit(app.exec_())