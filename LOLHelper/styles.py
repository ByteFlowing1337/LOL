MAIN_STYLE_SHEET = """
        QWidget {
            font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
            font-size: 14px;
            color: #2c3e50;
        }
        
        QMainWindow {
            background: #f8fafc;
        }
        
        QGroupBox {
            font-weight: bold;
            font-size: 16px;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            margin-top: 1.5ex;
            background: white;
            padding: 15px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 15px;
            color: #3b82f6;
            font-size: 16px;
            font-weight: bold;
            background: transparent;
        }
        
        QLabel {
            color: #334155;
            font-size: 14px;
        }
        
        QLineEdit, QComboBox {
            padding: 8px 12px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            background: white;
            min-height: 20px;
            selection-background-color: #3b82f6;
            selection-color: white;
        }
        
        QLineEdit:focus, QComboBox:focus {
            border: 2px solid #3b82f6;
            background: #f0f9ff;
        }
        
        QLineEdit:hover, QComboBox:hover {
            border: 2px solid #93c5fd;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #64748b;
            margin-right: 8px;
        }
        
        QComboBox:on {
            border: 2px solid #3b82f6;
        }
        
        QComboBox QAbstractItemView {
            border: 2px solid #3b82f6;
            border-radius: 8px;
            background: white;
            selection-background-color: #f0f9ff;
            selection-color: #2c3e50;
        }
        
        QPushButton {
            padding: 8px 16px;
            border-radius: 8px;
            border: none;
            font-weight: bold;
            min-width: 100px;
            min-height: 20px;
            background: #3b82f6;
            color: white;
        }
        
        QPushButton:hover {
            background: #2563eb;
        }
        
        QPushButton:pressed {
            background: #1d4ed8;
        }
        
        QPushButton:disabled {
            background: #94a3b8;
        }
        
        QPushButton:checked {
            background: #059669;
        }
        
        QPushButton[text="❌ 退出"] {
            background: #ef4444;
            min-width: 80px;
        }
        
        QPushButton[text="❌ 退出"]:hover {
            background: #dc2626;
        }
        
        QProgressBar {
            border: none;
            border-radius: 8px;
            background: #e2e8f0;
            height: 16px;
            text-align: center;
            margin: 0px 10px;
            font-size: 12px;
            color: white;
        }
        
        QProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #2563eb);
            border-radius: 8px;
        }
        
        QTabWidget::pane {
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            background: white;
            top: -1px;
        }
        
        QTabBar::tab {
            background: #f1f5f9;
            border: none;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            padding: 8px 16px;
            margin-right: 4px;
            color: #64748b;
        }
        
        QTabBar::tab:selected {
            background: white;
            color: #3b82f6;
            font-weight: bold;
        }
        
        QTabBar::tab:hover {
            background: #e2e8f0;
        }
        
        QTextBrowser {
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            padding: 10px;
            selection-background-color: #3b82f6;
            selection-color: white;
        }
        
        QScrollBar:vertical {
            border: none;
            background: #f1f5f9;
            width: 10px;
            border-radius: 5px;
            margin: 0px;
        }
        
        QScrollBar::handle:vertical {
            background: #94a3b8;
            border-radius: 5px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background: #64748b;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QStatusBar {
            background: #f8fafc;
            color: #64748b;
            border-top: 1px solid #e2e8f0;
        }
   """