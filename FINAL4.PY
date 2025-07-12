import requests
from requests.auth import HTTPBasicAuth
import urllib3
import json
import os
import re
from datetime import datetime, timedelta, timezone
import chardet
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QTextEdit, QGroupBox,
    QStatusBar, QProgressBar, QMessageBox, QFileDialog,QTextBrowser
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QTextDocument, QTextImageFormat, QTextCursor
from PyQt5.QtGui import QDesktopServices
import tempfile

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 日志目录路径
LOG_DIR = r"D:\WeGameApps\英雄联盟\LeagueClient"

# 英雄ID到名称的映射
CHAMPION_MAP = {
266: "Aatrox",103: "Ahri",84: "Akali",166: "Akshan",12: "Alistar",799: "Ambessa",32: "Amumu",34: "Anivia",1: "Annie",523: "Aphelios",22: "Ashe",136: "Aurelion Sol",893: "Aurora",
268: "Azir",432: "Bard",200: "Bel'Veth",53: "Blitzcrank",63: "Brand",201: "Braum",233: "Briar",51: "Caitlyn",164: "Camille",69: "Cassiopeia",31: "Cho'Gath",
42: "Corki",122: "Darius",131: "Diana",119: "Draven",36: "Dr. Mundo",245: "Ekko",60: "Elise",28: "Evelynn",81: "Ezreal",9: "Fiddlesticks",114: "Fiora",
105: "Fizz",3: "Galio",41: "Gangplank",86: "Garen",150: "Gnar",79: "Gragas",104: "Graves",887: "Gwen",120: "Hecarim",74: "Heimerdinger",910: "Hwei",420: "Illaoi",
39: "Irelia",427: "Ivern",40: "Janna",59: "Jarvan IV",24: "Jax",126: "Jayce",202: "Jhin",222: "Jinx",145: "Kai'Sa",429: "Kalista",43: "Karma",30: "Karthus",
38: "Kassadin",55: "Katarina",10: "Kayle",141: "Kayn",85: "Kennen",121: "Kha'Zix",203: "Kindred",240: "Kled",96: "Kog'Maw",897: "K'Sante",7: "LeBlanc",
64: "Lee Sin",89: "Leona",876: "Lillia",127: "Lissandra",236: "Lucian",117: "Lulu",99: "Lux",54: "Malphite",90: "Malzahar",57: "Maokai",11: "Master Yi",
800: "Mel",902: "Milio",21: "MissFortune",62: "Wukong",82: "Mordekaiser",25: "Morgana",950: "Naafiri",267: "Nami",75: "Nasus",111: "Nautilus",518: "Neeko",
76: "Nidalee",895: "Nilah",56: "Nocturne",20: "Nunu & Willump",2: "Olaf",61: "Orianna",516: "Ornn",80: "Pantheon",78: "Poppy",555: "Pyke",246: "Qiyana",133: "Quinn",497: "Rakan",33: "Rammus",
421: "Rek'Sai",526: "Rell",888: "Renata Glasc",58: "Renekton",107: "Rengar",92: "Riven",68: "Rumble",13: "Ryze",360: "Samira",113: "Sejuani",235: "Senna",147: "Seraphine",
875: "Sett",35: "Shaco",98: "Shen",102: "Shyvana",27: "Singed",14: "Sion",15: "Sivir",72: "Skarner",901: "Smolder",37: "Sona",16: "Soraka",50: "Swain",517: "Sylas",
134: "Syndra",223: "Tahm Kench",163: "Taliyah",91: "Talon",44: "Taric",17: "Teemo",412: "Thresh",18: "Tristana",48: "Trundle",23: "Tryndamere",
4: "Twisted Fate",29: "Twitch",77: "Udyr",6: "Urgot",110: "Varus",67: "Vayne",45: "Veigar",161: "Vel'Koz",711: "Vex",254: "Vi",234: "Viego",112: "Viktor",
8: "Vladimir",106: "Volibear",19: "Warwick",498: "Xayah",101: "Xerath",5: "XinZhao",157: "Yasuo",777: "Yone",83: "Yorick",350: "Yuumi",154: "Zac",238: "Zed",
221: "Zeri",115: "Ziggs",26: "Zilean",142: "Zoe",143: "Zyra"
}

# 段位映射表（简化版）
RANK_MAP = {
    0: "黑铁", 1: "青铜", 2: "白银", 3: "黄金", 
    4: "铂金", 5: "钻石", 6: "大师", 7: "宗师", 8: "王者"
}

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


class ImageDownloaderThread(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, champion_names, parent=None):
        super().__init__(parent)
        self.champion_names = champion_names  # set of champion English names
        self.result = {}  # {champion_en: local_path}

    def run(self):
        import requests, tempfile, os
        for champion_en in self.champion_names:
            # Data Dragon CDN URL
            url = f"https://ddragon.leagueoflegends.com/cdn/14.13.1/img/champion/{champion_en}.png"
            try:
                temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                response = requests.get(url, stream=True, timeout=10)
                if response.status_code == 200:
                    with open(temp.name, 'wb') as f:
                        f.write(response.content)
                    self.result[champion_en] = temp.name
                else:
                    self.result[champion_en] = url  # fallback to network url
            except Exception:
                self.result[champion_en] = url
        self.finished.emit(self.result)


class LOLMatchHistoryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.auth_token = None
        self.app_port = None
        self.summoner_name = ""
        self.temp_files = []  # 存储临时图片路径
        self.init_ui()
        self.autodetect_params()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("英雄联盟比赛记录获取工具")
        self.setGeometry(300, 200, 800, 600)
        self.setWindowIcon(QIcon("lol_icon.ico"))
        
        # 创建主部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("英雄联盟比赛记录获取工具")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #1e90ff; padding: 10px;")
        main_layout.addWidget(title_label)
        
        # 参数组
        param_group = QGroupBox("连接参数")
        param_layout = QVBoxLayout()
        
        # 自动检测区域
        auto_layout = QHBoxLayout()
        self.auto_detect_btn = QPushButton("自动检测参数")
        self.auto_detect_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        self.auto_detect_btn.clicked.connect(self.autodetect_params)
        auto_layout.addWidget(self.auto_detect_btn)
        
        self.param_status = QLabel("状态: 等待检测...")
        self.param_status.setStyleSheet("color: #666;")
        auto_layout.addWidget(self.param_status)
        param_layout.addLayout(auto_layout)
        
        # 手动输入区域
        manual_layout = QVBoxLayout()
        
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("认证令牌:"))
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("自动获取或手动输入")
        token_layout.addWidget(self.token_input)
        manual_layout.addLayout(token_layout)
        
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("应用端口:"))
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("自动获取或手动输入")
        port_layout.addWidget(self.port_input)
        manual_layout.addLayout(port_layout)
        
        param_layout.addLayout(manual_layout)
        param_group.setLayout(param_layout)
        main_layout.addWidget(param_group)
        
        # 召唤师输入区域
        summoner_group = QGroupBox("召唤师信息")
        summoner_layout = QVBoxLayout()
        
        summoner_input_layout = QHBoxLayout()
        summoner_input_layout.addWidget(QLabel("召唤师名称:"))
        self.summoner_input = QLineEdit()
        self.summoner_input.setPlaceholderText("输入您的召唤师名称")
        summoner_input_layout.addWidget(self.summoner_input)
        summoner_layout.addLayout(summoner_input_layout)
        
        summoner_group.setLayout(summoner_layout)
        main_layout.addWidget(summoner_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.fetch_btn = QPushButton("获取比赛记录")
        self.fetch_btn.setStyleSheet("background-color: #1e90ff; color: white; font-weight: bold;")
        self.fetch_btn.clicked.connect(self.start_fetching)
        self.fetch_btn.setEnabled(False)
        button_layout.addWidget(self.fetch_btn)
        
        self.save_btn = QPushButton("保存数据")
        self.save_btn.setStyleSheet("background-color: #FF8C00; color: white;")
        self.save_btn.clicked.connect(self.save_data)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)
        
        self.exit_btn = QPushButton("退出")
        self.exit_btn.setStyleSheet("background-color: #dc3545; color: white;")
        self.exit_btn.clicked.connect(self.close)
        button_layout.addWidget(self.exit_btn)
        
        main_layout.addLayout(button_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
                text-align: center;
                background: white;
            }
            QProgressBar::chunk {
                background-color: #1e90ff;
                width: 10px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("准备就绪")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: #666;")
        main_layout.addWidget(self.progress_label)
        
        # 结果显示区域
        result_group = QGroupBox("比赛记录")
        result_layout = QVBoxLayout()
        
        self.result_display = QTextBrowser()
        self.result_display.setReadOnly(True)
        self.result_display.setStyleSheet("background-color: #f8f9fa;")
        self.result_display.setOpenLinks(False)  # 禁用链接自动打开
        self.result_display.anchorClicked.connect(self.open_champion_url)  # 处理图片点击事件
        result_layout.addWidget(self.result_display)
        
        result_group.setLayout(result_layout)
        main_layout.addWidget(result_group)
        
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
                self.param_status.setStyleSheet("color: green;")
                self.fetch_btn.setEnabled(True)
                self.progress_bar.setValue(100)
                self.progress_label.setText("参数检测完成!")
                return
            else:
                self.param_status.setText("⚠️ 自动获取失败，请手动输入")
                self.param_status.setStyleSheet("color: orange;")
        else:
            self.param_status.setText("⚠️ 未找到日志文件，请确保游戏已运行")
            self.param_status.setStyleSheet("color: orange;")
        
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
        self.result_display.clear()
        self.progress_bar.setValue(0)
        self.progress_label.setText("开始获取数据...")
        self.save_btn.setEnabled(False)
        
        # 创建工作线程
        self.worker_thread = WorkerThread(self.auth_token, self.app_port, self.summoner_name)
        self.worker_thread.progress.connect(self.update_progress)
        self.worker_thread.result.connect(self.display_result)
        self.worker_thread.error.connect(self.show_error)
        self.worker_thread.start()
        
    def update_progress(self, value, message):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
        
    def download_image(self, url):
        """下载图片到临时文件，返回本地路径"""
        try:
            temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            self.temp_files.append(temp.name)
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(temp.name, 'wb') as f:
                    f.write(response.content)
                return temp.name
            return None
        except Exception as e:
            print(f"下载图片出错: {e}")
            return None

    def closeEvent(self, event):
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                print(f"删除临时文件出错: {e}")
        event.accept()


    def display_result(self, match_history, puuid):
        """显示结果（异步图片下载）"""
        self.match_history = match_history
        self.puuid = puuid
        self.save_btn.setEnabled(True)

        games = match_history.get('games', {}).get('games', [])[:20]
        total_count = match_history.get('totalCount', 0)

        # 收集所有用到的champion_en
        champion_names = set()
        for game in games:
            for participant in game.get('participants', []):
                champion_id = participant.get('championId')
                champion_en = CHAMPION_MAP.get(champion_id, f"Unknown_{champion_id}")
                champion_names.add(champion_en)
                break

        # 先用网络图片URL生成HTML
        self._champion_names_for_img = champion_names
        self._games_for_img = games
        self._result_html_args = (games, total_count)
        self._img_local_map = None
        self._refresh_result_html(img_map=None)

        # 启动图片下载线程
        self.img_thread = ImageDownloaderThread(champion_names)
        self.img_thread.finished.connect(self._on_img_downloaded)
        self.img_thread.start()

    def _on_img_downloaded(self, img_map):
        # 保存临时文件用于后续清理
        for path in img_map.values():
            if path.startswith("/") or path.startswith("C:") or path.startswith("D:") or path.startswith("E:"):
                if os.path.exists(path):
                    self.temp_files.append(path)
        self._img_local_map = img_map
        self._refresh_result_html(img_map=img_map)

    def _refresh_result_html(self, img_map=None):
        # 生成HTML，img_map为{champion_en: local_path or url}
        games, total_count = self._games_for_img, self._result_html_args[1]
        result_text = f"<h2>比赛记录 - {self.summoner_name}</h2>"
        if total_count >= 0:
            total_kills = total_deaths = total_assists = wins = losses = 0
            for game in games:
                for participant in game.get('participants', []):
                    stats = participant.get('stats', {})
                    total_kills += stats.get('kills', 0)
                    total_deaths += stats.get('deaths', 0)
                    total_assists += stats.get('assists', 0)
                    if stats.get('win', False):
                        wins += 1
                    else:
                        losses += 1
                    break
            avg_kills = total_kills / len(games) if games else 0
            avg_deaths = total_deaths / len(games) if games else 0
            avg_assists = total_assists / len(games) if games else 0
            avg_kda = (total_kills + total_assists) / total_deaths if total_deaths > 0 else 0
            win_rate = wins / len(games) * 100 if games else 0
            rank_level = min(8, max(0, int(win_rate / 12.5)))
            result_text += f"<div style='background-color:#f0f8ff; padding:10px; border-radius:5px; margin-bottom:15px;'>"
            result_text += f"<h3>最近20场比赛统计</h3>"
            result_text += f"<p><b>胜率:</b> {wins}胜{losses}负 ({win_rate:.1f}%)</p>"
            result_text += f"<p><b>平均KDA:</b> {avg_kda:.1f}</p>"
            result_text += f"<p><b>段位评估:</b> {RANK_MAP.get(rank_level, '未知')} ({rank_level}级)</p>"
            result_text += "</div>"
            result_text += f"<p><b>最近5场比赛详情:</b></p>"
            for i, game in enumerate(games, 1):
                result_text += f"<hr><h3>比赛 #{i}</h3>"
                result_text += f"<p><b>模式:</b> {game.get('gameMode', '未知模式')}</p>"
                result_text += f"<p><b>类型:</b> {game.get('gameType', '未知类型')}</p>"
                raw_date = game.get('gameCreationDate', '')
                if raw_date:
                    try:
                        utc_time = datetime.fromisoformat(raw_date.replace('Z', '+00:00'))
                        beijing_time = utc_time.astimezone(timezone(timedelta(hours=8)))
                        display_time = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        display_time = "时间解析错误"
                else:
                    display_time = "未知时间"
                result_text += f"<p><b>开始时间:</b> {display_time} </p>"
                duration = game.get('gameDuration', 0)
                minutes, seconds = divmod(duration, 60)
                result_text += f"<p><b>持续时间:</b> {minutes}分{seconds}秒</p>"
                for participant in game.get('participants', []):
                    champion_id = participant.get('championId')
                    champion_en = CHAMPION_MAP.get(champion_id, f"Unknown_{champion_id}")
                    stats = participant.get('stats', {})
                    # 图片URL
                    if img_map and champion_en in img_map:
                        img_src = img_map[champion_en]
                        if os.path.exists(img_src):
                            img_src = 'file:///' + img_src.replace('\\', '/')
                    else:
                        img_src = f"https://ddragon.leagueoflegends.com/cdn/14.13.1/img/champion/{champion_en}.png"
                    result_text += f"<p><b>英雄:</b> <img src='{img_src}' width='48' height='48' style='vertical-align:middle;margin-right:8px;'> {champion_en}</p>"
                    result_text += f"<p><b>KDA:</b> {stats.get('kills', 0)}/{stats.get('deaths', 0)}/{stats.get('assists', 0)}</p>"
                    win_color = "green" if stats.get('win', False) else "red"
                    result_text += f"<p><b>结果:</b> <span style='color:{win_color};font-weight:bold;'>"
                    result_text += "胜利" if stats.get('win', False) else "失败"
                    result_text += "</span></p>"
                    break
        self.result_display.setHtml(result_text)
        self.status_bar.showMessage("数据获取完成")
        
    def open_champion_url(self, url):
        """打开英雄详情页面"""
        QDesktopServices.openUrl(url)
        
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
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #ccc;
            border-radius: 5px;
            margin-top: 1ex;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 5px;
        }
        QPushButton {
            padding: 5px 10px;
            border-radius: 4px;
            min-width: 80px;
        }
        QLineEdit, QTextEdit {
            padding: 5px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        QTextEdit {
            font-family: 'Consolas', 'Courier New', monospace;
        }
        QProgressBar {
            height: 20px;
        }
    """)
    
    window = LOLMatchHistoryApp()
    window.show()
    sys.exit(app.exec_())