import requests
from requests.auth import HTTPBasicAuth
import urllib3
import json
import os
import re
from datetime import datetime, timedelta
import chardet
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QTextEdit, QGroupBox,
    QStatusBar, QProgressBar, QMessageBox, QFileDialog,
    QFrame, QScrollArea, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QLinearGradient, QPen, QBrush
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 日志目录路径
LOG_DIR = r"D:\WeGameApps\英雄联盟\LeagueClient"

class WorkerThread(QThread):
    progress = pyqtSignal(int, str)
    result = pyqtSignal(dict, str)
    error = pyqtSignal(str)

    def __init__(self, auth_token, app_port, summoner_name):
        super().__init__()
        self.auth_token = auth_token
        self.app_port = app_port
        self.summoner_name = summoner_name

    def run(self):
        try:
            # 获取PUUID
            self.progress.emit(30, "正在获取PUUID...")
            puuid = self.get_puuid()
            
            if not puuid:
                self.error.emit("无法获取PUUID，请检查召唤师名称")
                return
            
            self.progress.emit(50, f"成功获取PUUID: {puuid}")
            
            # 获取比赛记录
            self.progress.emit(60, "正在获取比赛记录...")
            match_history = self.get_match_history(puuid)
            
            if match_history:
                self.progress.emit(100, "比赛记录获取成功!")
                self.result.emit(match_history, puuid)
            else:
                self.error.emit("无法获取比赛记录")
                
        except Exception as e:
            self.error.emit(f"发生错误: {str(e)}")

    def get_puuid(self):
        """获取召唤师的PUUID"""
        url = f"https://riot:{self.auth_token}@127.0.0.1:{self.app_port}/lol-summoner/v1/summoners"
        try:
            response = requests.get(
                url,
                params={'name': self.summoner_name},
                auth=HTTPBasicAuth('riot', self.auth_token),
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('puuid')
            else:
                self.error.emit(f"获取PUUID失败! 状态码: {response.status_code}\n响应内容: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.error.emit(f"请求异常: {e}")
            return None

    def get_match_history(self, puuid):
        """获取比赛历史记录"""
        url = f"https://riot:{self.auth_token}@127.0.0.1:{self.app_port}/lol-match-history/v1/products/lol/{puuid}/matches"
        try:
            response = requests.get(
                url,
                auth=HTTPBasicAuth('riot', self.auth_token),
                verify=False,
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.error.emit(f"获取比赛记录失败! 状态码: {response.status_code}\n响应内容: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.error.emit(f"请求异常: {e}")
            return None


class KDACanvas(FigureCanvas):
    """自定义KDA可视化图表"""
    def __init__(self, kills, deaths, assists, width=5, height=3, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#f0f0f0')
        super(KDACanvas, self).__init__(self.fig)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.kills = kills
        self.deaths = deaths
        self.assists = assists
        self.draw_kda_chart()

    def draw_kda_chart(self):
        """绘制KDA图表"""
        ax = self.fig.add_subplot(111)
        
        # 计算KDA比率（防止除零错误）
        if self.deaths == 0:
            kda_ratio = self.kills + self.assists
        else:
            kda_ratio = (self.kills + self.assists) / self.deaths
        
        # 数据
        labels = ['击杀', '死亡', '助攻']
        values = [self.kills, self.deaths, self.assists]
        colors = ['#4CAF50', '#F44336', '#2196F3']  # 绿、红、蓝
        
        # 绘制柱状图
        bars = ax.bar(labels, values, color=colors)
        
        # 在柱子上方显示数值
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height}', ha='center', va='bottom', fontsize=12)
        
        # 添加KDA比率
        ax.text(0.5, 0.95, f'KDA比率: {kda_ratio:.2f}', 
                transform=ax.transAxes, ha='center', va='top', fontsize=12,
                bbox=dict(facecolor='gold', alpha=0.5))
        
        # 设置标题和标签
        ax.set_title('比赛KDA数据', fontsize=14)
        ax.set_ylabel('数量', fontsize=10)
        
        # 设置网格
        ax.grid(True, linestyle='--', alpha=0.3)
        
        # 移除上、右边框
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        self.fig.tight_layout()


class LOLMatchHistoryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.auth_token = None
        self.app_port = None
        self.summoner_name = ""
        self.init_ui()
        self.autodetect_params()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("英雄联盟比赛记录获取工具")
        self.setGeometry(300, 200, 1000, 700)
        self.setWindowIcon(QIcon("lol_icon.ico"))
        
        # 创建主部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题
        title_label = QLabel("英雄联盟比赛记录获取工具")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            color: #1e90ff; 
            padding: 15px; 
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1e3c72, stop:1 #2a5298);
            border-radius: 10px;
            color: white;
        """)
        main_layout.addWidget(title_label)
        
        # 参数组
        param_group = QGroupBox("连接参数")
        param_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        param_layout = QVBoxLayout()
        param_layout.setSpacing(10)
        
        # 自动检测区域
        auto_layout = QHBoxLayout()
        self.auto_detect_btn = QPushButton("自动检测参数")
        self.auto_detect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.auto_detect_btn.clicked.connect(self.autodetect_params)
        auto_layout.addWidget(self.auto_detect_btn)
        
        self.param_status = QLabel("状态: 等待检测...")
        self.param_status.setStyleSheet("color: #666; font-size: 12px;")
        auto_layout.addWidget(self.param_status)
        auto_layout.addStretch()
        param_layout.addLayout(auto_layout)
        
        # 手动输入区域
        manual_layout = QGridLayout()
        manual_layout.setSpacing(10)
        
        manual_layout.addWidget(QLabel("认证令牌:"), 0, 0)
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("自动获取或手动输入")
        self.token_input.setMinimumHeight(30)
        manual_layout.addWidget(self.token_input, 0, 1)
        
        manual_layout.addWidget(QLabel("应用端口:"), 1, 0)
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("自动获取或手动输入")
        self.port_input.setMinimumHeight(30)
        manual_layout.addWidget(self.port_input, 1, 1)
        
        param_layout.addLayout(manual_layout)
        param_group.setLayout(param_layout)
        main_layout.addWidget(param_group)
        
        # 召唤师输入区域
        summoner_group = QGroupBox("召唤师信息")
        summoner_layout = QHBoxLayout()
        
        summoner_layout.addWidget(QLabel("召唤师名称:"))
        self.summoner_input = QLineEdit()
        self.summoner_input.setPlaceholderText("输入您的召唤师名称")
        self.summoner_input.setMinimumHeight(35)
        self.summoner_input.setStyleSheet("font-size: 14px;")
        summoner_layout.addWidget(self.summoner_input, 1)
        
        summoner_group.setLayout(summoner_layout)
        main_layout.addWidget(summoner_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.fetch_btn = QPushButton("获取比赛记录")
        self.fetch_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e90ff; 
                color: white; 
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #1c86ee;
            }
            QPushButton:disabled {
                background-color: #b0c4de;
            }
        """)
        self.fetch_btn.clicked.connect(self.start_fetching)
        self.fetch_btn.setEnabled(False)
        button_layout.addWidget(self.fetch_btn)
        
        self.save_btn = QPushButton("保存数据")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF8C00; 
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #ff7f00;
            }
            QPushButton:disabled {
                background-color: #ffcc99;
            }
        """)
        self.save_btn.clicked.connect(self.save_data)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)
        
        self.exit_btn = QPushButton("退出")
        self.exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545; 
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.exit_btn.clicked.connect(self.close)
        button_layout.addWidget(self.exit_btn)
        
        main_layout.addLayout(button_layout)
        
        # 进度条
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(5)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
                text-align: center;
                background: white;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #1e90ff;
                border-radius: 5px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("准备就绪")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: #666; font-size: 12px;")
        progress_layout.addWidget(self.progress_label)
        
        main_layout.addLayout(progress_layout)
        
        # 结果显示区域 - 使用滚动区域
        result_scroll = QScrollArea()
        result_scroll.setWidgetResizable(True)
        result_scroll.setStyleSheet("background: transparent; border: none;")
        
        result_container = QWidget()
        self.result_layout = QVBoxLayout(result_container)
        self.result_layout.setSpacing(20)
        self.result_layout.setAlignment(Qt.AlignTop)
        
        # 添加一个初始提示标签
        self.placeholder_label = QLabel("比赛记录将在这里显示")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("color: #888; font-size: 16px; padding: 50px;")
        self.result_layout.addWidget(self.placeholder_label)
        
        result_scroll.setWidget(result_container)
        
        main_layout.addWidget(result_scroll)
        
        # 设置主布局
        main_widget.setLayout(main_layout)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 工作线程
        self.worker_thread = None
        
    def autodetect_params(self):
        """自动检测参数"""
        self.progress_label.setText("正在检测参数...")
        self.progress_bar.setValue(10)
        
        log_file = self.get_latest_log_file()
        
        if log_file:
            self.status_bar.showMessage(f"找到日志文件: {os.path.basename(log_file)}")
            auth_token, app_port = self.extract_params_from_log(log_file)
            
            if auth_token and app_port:
                self.auth_token = auth_token
                self.app_port = app_port
                self.token_input.setText(auth_token)
                self.port_input.setText(str(app_port))
                self.param_status.setText("✅ 自动获取成功!")
                self.param_status.setStyleSheet("color: green; font-weight: bold;")
                self.fetch_btn.setEnabled(True)
                self.progress_bar.setValue(100)
                self.progress_label.setText("参数检测完成!")
                return
            else:
                self.param_status.setText("⚠️ 自动获取失败，请手动输入")
                self.param_status.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.param_status.setText("⚠️ 未找到日志文件，请确保游戏已运行")
            self.param_status.setStyleSheet("color: orange; font-weight: bold;")
        
        self.progress_bar.setValue(0)
        self.progress_label.setText("参数检测完成")

    def get_latest_log_file(self):
        """获取最新的日志文件"""
        try:
            # 列出所有日志文件
            log_files = [f for f in os.listdir(LOG_DIR) 
                        if f.endswith("_LeagueClientUx.log") and "T" in f]
            
            if not log_files:
                return None
            
            # 提取文件名中的时间戳并排序
            def extract_time(f):
                try:
                    # 文件名格式: 2025-07-12T12-23-05_18520_LeagueClientUx.log
                    time_str = f.split("T")[0] + "T" + f.split("T")[1].split("_")[0]
                    return datetime.strptime(time_str, "%Y-%m-%dT%H-%M-%S")
                except:
                    return datetime.min
            
            # 获取最新文件
            latest_file = max(log_files, key=extract_time)
            return os.path.join(LOG_DIR, latest_file)
        
        except Exception as e:
            self.status_bar.showMessage(f"获取日志文件时出错: {e}")
            return None

    def detect_file_encoding(self, file_path):
        """检测文件编码"""
        try:
            # 读取文件开头部分内容检测编码
            with open(file_path, 'rb') as f:
                raw_data = f.read(4096)
                result = chardet.detect(raw_data)
                return result['encoding'] or 'gbk'
        except Exception as e:
            self.status_bar.showMessage(f"检测文件编码失败: {e}, 默认使用GBK")
            return 'gbk'

    def extract_params_from_log(self, log_file):
        """从日志文件中提取认证令牌和端口号"""
        try:
            # 检测文件编码
            encoding = self.detect_file_encoding(log_file)
            self.status_bar.showMessage(f"检测到文件编码: {encoding}")
            
            with open(log_file, "r", encoding=encoding, errors='replace') as f:
                # 读取前7行（第7行包含参数）
                for i in range(7):
                    line = f.readline().strip()
                    if i == 6:  # 第7行
                        # 使用正则表达式提取参数
                        token_match = re.search(r"--remoting-auth-token=([\w-]+)", line)
                        port_match = re.search(r"--app-port=(\d+)", line)
                        
                        if token_match and port_match:
                            return token_match.group(1), int(port_match.group(1))
                        else:
                            self.status_bar.showMessage(f"参数提取失败，第7行内容: {line[:100]}...")
            return None, None
        except Exception as e:
            self.status_bar.showMessage(f"读取日志文件时出错: {e}")
            return None, None

    def start_fetching(self):
        """开始获取比赛记录"""
        # 获取输入参数
        self.auth_token = self.token_input.text().strip()
        port_text = self.port_input.text().strip()
        self.summoner_name = self.summoner_input.text().strip()
        
        # 验证输入
        if not self.auth_token:
            QMessageBox.warning(self, "输入错误", "认证令牌不能为空")
            return
            
        try:
            self.app_port = int(port_text)
        except ValueError:
            QMessageBox.warning(self, "输入错误", "端口号必须是数字")
            return
            
        if not self.summoner_name:
            QMessageBox.warning(self, "输入错误", "召唤师名称不能为空")
            return
            
        # 重置UI状态
        self.clear_results()
        self.progress_bar.setValue(0)
        self.progress_label.setText("开始获取数据...")
        self.save_btn.setEnabled(False)
        
        # 创建工作线程
        self.worker_thread = WorkerThread(self.auth_token, self.app_port, self.summoner_name)
        self.worker_thread.progress.connect(self.update_progress)
        self.worker_thread.result.connect(self.display_result)
        self.worker_thread.error.connect(self.show_error)
        self.worker_thread.start()
        
    def clear_results(self):
        """清除现有结果"""
        # 移除所有比赛记录部件
        for i in reversed(range(self.result_layout.count())):
            widget = self.result_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # 重新添加占位符
        self.placeholder_label = QLabel("正在获取比赛记录...")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("color: #888; font-size: 16px; padding: 50px;")
        self.result_layout.addWidget(self.placeholder_label)
        
    def update_progress(self, value, message):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
        
    def display_result(self, match_history, puuid):
        """显示结果"""
        # 移除占位符标签
        if self.placeholder_label:
            self.placeholder_label.deleteLater()
            self.placeholder_label = None
        
        self.match_history = match_history
        self.puuid = puuid
        self.save_btn.setEnabled(True)
        
        # 提取最近的5场比赛
        games = match_history.get('games', {}).get('games', [])[:5]
        total_count = match_history.get('totalCount', 0)
        
        # 添加比赛记录标题
        title_label = QLabel(f"{self.summoner_name}的最近{len(games)}场比赛")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title_label.setStyleSheet("color: #1e3c72; padding: 10px 0;")
        self.result_layout.addWidget(title_label)
        
        # 添加比赛总数
      ##  count_label = QLabel(f"总比赛场次: {total_count}")
     #   count_label.setFont(QFont("Microsoft YaHei", 10))
      #  count_label.setStyleSheet("color: #555; padding-bottom: 10px;")
      #  self.result_layout.addWidget(count_label)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #ddd;")
        self.result_layout.addWidget(separator)
        
        if total_count >= 0:
            for i, game in enumerate(games, 1):
                self.add_game_widget(i, game, puuid)
        
        self.status_bar.showMessage("数据获取完成")
        
    def add_game_widget(self, game_index, game, puuid):
        """添加单个比赛的显示部件"""
        # 创建比赛容器
        game_frame = QFrame()
        game_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        game_layout = QVBoxLayout(game_frame)
        game_layout.setSpacing(10)
        
        # 比赛标题
        title_label = QLabel(f"比赛 #{game_index}")
        title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        title_label.setStyleSheet("color: #1e3c72;")
        game_layout.addWidget(title_label)
        
        # 基本信息布局
        info_layout = QGridLayout()
        info_layout.setColumnStretch(1, 1)
        info_layout.setSpacing(8)
        
        # 游戏模式
        info_layout.addWidget(QLabel("模式:"), 0, 0)
        mode_label = QLabel(game.get('gameMode', '未知模式'))
        mode_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(mode_label, 0, 1)
        
        # 游戏类型
        info_layout.addWidget(QLabel("类型:"), 1, 0)
        type_label = QLabel(game.get('gameType', '未知类型'))
        type_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(type_label, 1, 1)
        
        # 开始时间
        info_layout.addWidget(QLabel("开始时间:"), 2, 0)
        time_str = game.get('gameCreationDate', '未知时间')
        # 尝试解析时间格式
        try:
            # 原始格式: "2025-07-12T03:22:05.123Z"
            dt = datetime.strptime(time_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
            beijing_time = dt + timedelta(hours=8)
            time_label = QLabel(beijing_time.strftime("%Y-%m-%d %H:%M:%S"))
        except:
            time_label = QLabel(time_str)
        info_layout.addWidget(time_label, 2, 1)
        
        # 持续时间
        info_layout.addWidget(QLabel("持续时间:"), 3, 0)
        duration = game.get('gameDuration', 0)
        minutes, seconds = divmod(duration, 60)
        duration_label = QLabel(f"{minutes}分{seconds}秒")
        info_layout.addWidget(duration_label, 3, 1)
        
        game_layout.addLayout(info_layout)
        
        # 查找玩家数据
        player_stats = None
        for participant in game.get('participants', []):
          
                player_stats = participant.get('stats', {})
                break
        
        if player_stats:
            # 玩家数据布局
            player_layout = QGridLayout()
            player_layout.setColumnStretch(1, 1)
            player_layout.setSpacing(8)
            
            # 英雄ID
            player_layout.addWidget(QLabel("英雄ID:"), 0, 0)
            champ_label = QLabel(str(participant.get('championId', '未知')))
            player_layout.addWidget(champ_label, 0, 1)
            
            # KDA
            kills = player_stats.get('kills', 0)
            deaths = player_stats.get('deaths', 0)
            assists = player_stats.get('assists', 0)
            
            player_layout.addWidget(QLabel("K/D/A:"), 1, 0)
            kda_label = QLabel(f"{kills}/{deaths}/{assists}")
            kda_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            player_layout.addWidget(kda_label, 1, 1)
            
            # 结果
            player_layout.addWidget(QLabel("结果:"), 2, 0)
            win = player_stats.get('win', False)
            result_label = QLabel("胜利" if win else "失败")
            result_label.setStyleSheet(f"color: {'green' if win else 'red'}; font-weight: bold;")
            player_layout.addWidget(result_label, 2, 1)
            
            game_layout.addLayout(player_layout)
            
            # 添加KDA图表
            kda_chart = KDACanvas(kills, deaths, assists, width=4, height=2.5)
            game_layout.addWidget(kda_chart)
            
        else:
            # 没有找到玩家数据
            error_label = QLabel("⚠️ 未找到玩家数据")
            error_label.setStyleSheet("color: red; font-weight: bold;")
            game_layout.addWidget(error_label)
        
        # 添加到结果布局
        self.result_layout.addWidget(game_frame)
        
    def show_error(self, message):
        """显示错误信息"""
        QMessageBox.critical(self, "错误", message)
        self.progress_bar.setValue(0)
        self.progress_label.setText("操作失败")
        
    def save_data(self):
        """保存数据到文件"""
        if not hasattr(self, 'match_history'):
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "保存比赛记录", 
            "", 
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                # 确保文件扩展名
                if not file_path.lower().endswith('.json'):
                    file_path += '.json'
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.match_history, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(self, "保存成功", f"数据已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"保存文件时出错:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 设置应用样式
    app.setStyleSheet("""
        QWidget {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            font-size: 12px;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 15px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 10px;
            background-color: transparent;
        }
        QPushButton {
            padding: 8px 15px;
            border-radius: 5px;
            min-width: 100px;
            border: none;
        }
        QLineEdit, QTextEdit {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: white;
        }
        QLineEdit:focus, QTextEdit:focus {
            border: 1px solid #1e90ff;
        }
        QProgressBar {
            height: 25px;
            border-radius: 4px;
        }
        QScrollArea {
            background: transparent;
            border: none;
        }
    """)
    
    window = LOLMatchHistoryApp()
    window.show()
    sys.exit(app.exec_())