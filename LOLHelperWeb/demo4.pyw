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
    QStatusBar, QProgressBar, QMessageBox, QFileDialog, QTextBrowser,
    QTabWidget, QScrollArea,QComboBox, QGridLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QFont, QIcon, QTextDocument, QTextImageFormat, QTextCursor, QGuiApplication
from PyQt5.QtGui import QDesktopServices
import tempfile
import ctypes
from PyQt5 import QtCore

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def download_app_icon():
    """下载并保存应用图标"""
    icon_url = "https://ts1.tc.mm.bing.net/th/id/R-C.b6bda78bb2c0556890e99189ee6c7cf8?rik=BWtX0xPRdhcVzQ&riu=http%3a%2f%2f5b0988e595225.cdn.sohucs.com%2fimages%2f20190919%2f8fee0a05727549a9a755cd2bac843914.jpeg&ehk=MEHswKpq23dWA1xiGud%2fop7%2fqmEqTQUXUQBdIYEvMtM%3d&risl=&pid=ImgRaw&r=0"
    icon_path = os.path.join(tempfile.gettempdir(), "lol_icon.ico")
    
    try:
        if not os.path.exists(icon_path):
            response = requests.get(icon_url)
            if response.status_code == 200:
                with open(icon_path, "wb") as f:
                    f.write(response.content)
        return icon_path
    except Exception as e:
        print(f"下载图标失败: {e}")
        return None

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

CHAMPION_ZH_MAP = {
    "Aatrox": "亚托克斯", "Ahri": "阿狸", "Akali": "阿卡丽", "Akshan": "阿克尚", "Alistar": "阿利斯塔",
    "Ambessa": "安蓓萨", "Amumu": "阿木木", "Anivia": "艾尼维亚", "Annie": "安妮", "Aphelios": "厄斐琉斯",
    "Ashe": "艾希", "Aurelion Sol": "奥瑞利安·索尔", "Aurora": "奥罗拉", "Azir": "阿兹尔", "Bard": "巴德",
    "Bel'Veth": "卑尔维斯", "Blitzcrank": "布里茨", "Brand": "布兰德", "Braum": "布隆", "Briar": "百裂冥犬",
    "Caitlyn": "凯特琳", "Camille": "卡蜜尔", "Cassiopeia": "卡西奥佩娅", "Cho'Gath": "科加斯", "Corki": "库奇",
    "Darius": "德莱厄斯", "Diana": "黛安娜", "Draven": "德莱文", "Dr. Mundo": "蒙多医生", "Ekko": "艾克",
    "Elise": "伊莉丝", "Evelynn": "伊芙琳", "Ezreal": "伊泽瑞尔", "Fiddlesticks": "费德提克", "Fiora": "菲奥娜",
    "Fizz": "菲兹", "Galio": "加里奥", "Gangplank": "普朗克", "Garen": "盖伦", "Gnar": "纳尔", "Gragas": "古拉加斯",
    "Graves": "格雷福斯", "Gwen": "格温", "Hecarim": "赫卡里姆", "Heimerdinger": "黑默丁格", "Hwei": "彗",
    "Illaoi": "俄洛伊", "Irelia": "艾瑞莉娅", "Ivern": "艾翁", "Janna": "迦娜", "Jarvan IV": "嘉文四世",
    "Jax": "贾克斯", "Jayce": "杰斯", "Jhin": "烬", "Jinx": "金克丝", "Kai'Sa": "卡莎", "Kalista": "卡莉丝塔",
    "Karma": "卡尔玛", "Karthus": "卡尔萨斯", "Kassadin": "卡萨丁", "Katarina": "卡特琳娜", "Kayle": "凯尔",
    "Kayn": "凯隐", "Kennen": "凯南", "Kha'Zix": "卡兹克", "Kindred": "千珏", "Kled": "克烈", "Kog'Maw": "克格莫",
    "K'Sante": "奎桑提", "LeBlanc": "乐芙兰", "Lee Sin": "李青", "Leona": "蕾欧娜", "Lillia": "莉莉娅",
    "Lissandra": "丽桑卓", "Lucian": "卢锡安", "Lulu": "璐璐", "Lux": "拉克丝", "Malphite": "墨菲特",
    "Malzahar": "玛尔扎哈", "Maokai": "茂凯", "Master Yi": "易", "Mel": "梅尔", "Milio": "米利欧",
    "MissFortune": "厄运小姐", "Wukong": "孙悟空", "Mordekaiser": "莫德凯撒", "Morgana": "莫甘娜", "Naafiri": "纳亚菲利",
    "Nami": "娜美", "Nasus": "内瑟斯", "Nautilus": "诺提勒斯", "Neeko": "妮蔻", "Nidalee": "奈德丽", "Nilah": "尼菈",
    "Nocturne": "魔腾", "Nunu & Willump": "努努和威朗普", "Olaf": "奥拉夫", "Orianna": "奥莉安娜", "Ornn": "奥恩",
    "Pantheon": "潘森", "Poppy": "波比", "Pyke": "派克", "Qiyana": "奇亚娜", "Quinn": "奎因", "Rakan": "洛",
    "Rammus": "拉莫斯", "Rek'Sai": "雷克塞", "Rell": "芮尔", "Renata Glasc": "烈娜塔", "Renekton": "雷克顿",
    "Rengar": "雷恩加尔", "Riven": "锐雯", "Rumble": "兰博", "Ryze": "瑞兹", "Samira": "莎弥拉", "Sejuani": "瑟庄妮",
    "Senna": "赛娜", "Seraphine": "萨勒芬妮", "Sett": "瑟提", "Shaco": "萨科", "Shen": "慎", "Shyvana": "希瓦娜",
    "Singed": "辛吉德", "Sion": "赛恩", "Sivir": "希维尔", "Skarner": "斯卡纳", "Smolder": "斯莫德", "Sona": "娑娜",
    "Soraka": "索拉卡", "Swain": "斯维因", "Sylas": "塞拉斯", "Syndra": "辛德拉", "Tahm Kench": "塔姆",
    "Taliyah": "塔莉垭", "Talon": "泰隆", "Taric": "塔里克", "Teemo": "提莫", "Thresh": "锤石", "Tristana": "崔丝塔娜",
    "Trundle": "特朗德尔", "Tryndamere": "泰达米尔", "Twisted Fate": "崔斯特", "Twitch": "图奇", "Udyr": "乌迪尔",
    "Urgot": "厄加特", "Varus": "韦鲁斯", "Vayne": "薇恩", "Veigar": "维迦", "Vel'Koz": "维克兹", "Vex": "薇古丝",
    "Vi": "蔚", "Viego": "佛耶戈", "Viktor": "维克托", "Vladimir": "弗拉基米尔", "Volibear": "沃利贝尔",
    "Warwick": "沃里克", "Xayah": "霞", "Xerath": "泽拉斯", "XinZhao": "赵信", "Yasuo": "亚索", "Yone": "永恩",
    "Yorick": "约里克", "Yuumi": "悠米", "Zac": "扎克", "Zed": "劫", "Zeri": "泽丽", "Ziggs": "吉格斯",
    "Zilean": "基兰", "Zoe": "佐伊", "Zyra": "婕拉"
}

CHAMPION_ZH_TO_ID = {}
for id, en_name in CHAMPION_MAP.items():
    zh_name = CHAMPION_ZH_MAP.get(en_name, en_name)
    CHAMPION_ZH_TO_ID[zh_name] = id

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


class AutoAcceptThread(QThread):
    status_signal = pyqtSignal(str)  # 发送状态信息到UI
    teammate_signal = pyqtSignal(list)  # 发送队友puuid列表

    def __init__(self, auth_token, app_port):
        super().__init__()
        self.auth_token = auth_token
        self.app_port = app_port
        self.is_running = True
        self.last_phase = None
        self.processed_session = False

    def stop(self):
        self.is_running = False

    def run(self):
        while self.is_running:
            try:
                # 1. 检查游戏状态
                phase_url = f"https://riot:{self.auth_token}@127.0.0.1:{self.app_port}/lol-gameflow/v1/gameflow-phase"
                phase_response = requests.get(
                    phase_url,
                    verify=False,
                    timeout=5
                )
                
                if phase_response.status_code == 200:
                    current_phase = phase_response.json()
                    
                    # 如果阶段发生变化，重置processed_session标志
                    if current_phase != self.last_phase:
                        self.processed_session = False
                        self.last_phase = current_phase
                    
                    if current_phase == "ReadyCheck":
                        # 发现对局，自动接受
                        accept_url = f"https://riot:{self.auth_token}@127.0.0.1:{self.app_port}/lol-lobby-team-builder/v1/ready-check/accept"
                        accept_response = requests.post(
                            accept_url,
                            verify=False,
                            timeout=5
                        )
                        if accept_response.status_code == 204:
                            self.status_signal.emit("已自动接受对局")
                        else:
                            self.status_signal.emit(f"接受对局失败: {accept_response.status_code}")
                            
                    elif current_phase == "ChampSelect" and not self.processed_session:
                        # 进入英雄选择，获取队友信息
                        session_url = f"https://riot:{self.auth_token}@127.0.0.1:{self.app_port}/lol-champ-select/v1/session"
                        session_response = requests.get(
                            session_url,
                            verify=False,
                            timeout=5
                        )
                        
                        if session_response.status_code == 200:
                            session_data = session_response.json()
                            teammate_puuids = []
                            
                            # 解析我方队伍信息，获取真实puuid
                            for teammate in session_data.get('myTeam', []):
                                puuid = teammate.get('puuid')
                                if puuid and puuid != "":  # 只收集有效的puuid
                                    teammate_puuids.append({
                                        'puuid': puuid,
                                        'gameName': teammate.get('gameName', 'Unknown'),
                                        'tagLine': teammate.get('tagLine', '')
                                    })
                            
                            if teammate_puuids:
                                self.status_signal.emit(f"找到 {len(teammate_puuids)} 名队友")
                                self.teammate_signal.emit(teammate_puuids)
                                self.processed_session = True  # 标记已处理，避免重复发送
                
            except Exception as e:
                self.status_signal.emit(f"检查对局状态出错: {str(e)}")
            
            # 休眠1秒再检查
            QThread.sleep(1)


class TeammateWorkerThread(QThread):
    progress = pyqtSignal(int, str)
    result = pyqtSignal(dict, str, str, str)  # match_history, puuid, gameName, tagLine
    error = pyqtSignal(str)

    def __init__(self, auth_token, app_port, puuid, game_name, tag_line):
        super().__init__()
        self.auth_token = auth_token
        self.app_port = app_port
        self.puuid = puuid
        self.game_name = game_name
        self.tag_line = tag_line

    def run(self):
        try:
            self.progress.emit(60, f"正在获取 {self.game_name} 的比赛记录...")
            match_history = self.get_match_history()
            
            if match_history:
                self.progress.emit(100, "比赛记录获取成功!")
                self.result.emit(match_history, self.puuid, self.game_name, self.tag_line)
            else:
                self.error.emit(f"无法获取 {self.game_name} 的比赛记录")
                
        except Exception as e:
            self.error.emit(f"发生错误: {str(e)}")

    def get_match_history(self):
        """获取比赛历史记录"""
        url = f"https://riot:{self.auth_token}@127.0.0.1:{self.app_port}/lol-match-history/v1/products/lol/{self.puuid}/matches"
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
                self.error.emit(f"获取比赛记录失败! 状态码: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.error.emit(f"请求异常: {e}")
            return None


class LOLMatchHistoryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.auth_token = None
        self.app_port = None
        self.summoner_name = ""
        self.temp_files = []  # 存储临时图片路径
        self.auto_accept_thread = None
        self.init_ui()
        self.autodetect_params()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("英雄联盟数据助手")
        self.setGeometry(300, 200, 900, 700)  # 更大的窗口尺寸
        
        # 设置窗口图标
        icon_path = download_app_icon()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        
        # 创建主部件和布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)  # 增加控件间距
        main_layout.setContentsMargins(20, 20, 20, 20)  # 增加边距
        
        # 标题
        title_label = QLabel("英雄联盟数据助手")
        title_label.setFont(QFont("Microsoft YaHei", 24, QFont.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            color: #1976d2;
            padding: 20px;
            margin-bottom: 10px;
        """)
        main_layout.addWidget(title_label)
        
        # 参数组
        param_group = QGroupBox("连接配置")
        param_layout = QVBoxLayout()
        param_layout.setSpacing(15)
        
        # 自动检测区域
        auto_layout = QHBoxLayout()
        self.auto_detect_btn = QPushButton("🔄 自动检测")
        self.auto_detect_btn.clicked.connect(self.autodetect_params)
        auto_layout.addWidget(self.auto_detect_btn)
        
        self.param_status = QLabel("状态: 等待检测...")
        self.param_status.setStyleSheet("color: #666;")
        auto_layout.addWidget(self.param_status)
        param_layout.addLayout(auto_layout)
        
        # 手动输入区域
        manual_layout = QGridLayout()
        manual_layout.setSpacing(10)
        
        token_label = QLabel("认证令牌:")
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("自动获取或手动输入")
        manual_layout.addWidget(token_label, 0, 0)
        manual_layout.addWidget(self.token_input, 0, 1)
        
        port_label = QLabel("应用端口:")
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("自动获取或手动输入")
        manual_layout.addWidget(port_label, 1, 0)
        manual_layout.addWidget(self.port_input, 1, 1)
        
        param_layout.addLayout(manual_layout)
        param_group.setLayout(param_layout)
        main_layout.addWidget(param_group)
        
        # 召唤师信息组
        summoner_group = QGroupBox("召唤师信息")
        summoner_layout = QHBoxLayout()
        summoner_layout.setSpacing(10)
        
        name_label = QLabel("召唤师名称:")
        self.summoner_input = QLineEdit()
        self.summoner_input.setPlaceholderText("输入召唤师名称")
        summoner_layout.addWidget(name_label)
        summoner_layout.addWidget(self.summoner_input)
        
        summoner_group.setLayout(summoner_layout)
        main_layout.addWidget(summoner_group)
        
        # 英雄选择组
        hero_group = QGroupBox("英雄选择")
        hero_layout = QHBoxLayout()
        hero_layout.setSpacing(10)
        
        self.hero_search = QLineEdit()
        self.hero_search.setPlaceholderText("🔍 搜索英雄...")
        self.hero_search.textChanged.connect(self.filter_heroes)
        
        self.hero_combo = QComboBox()
        self.hero_combo.addItems(sorted(CHAMPION_ZH_TO_ID.keys()))
        
        self.auto_select_btn = QPushButton("自动选择")
        self.auto_select_btn.setCheckable(True)
        
        hero_layout.addWidget(self.hero_search)
        hero_layout.addWidget(self.hero_combo)
        hero_layout.addWidget(self.auto_select_btn)
        
        hero_group.setLayout(hero_layout)
        main_layout.addWidget(hero_group)
        
        # 操作按钮组
        button_group = QGroupBox("操作")
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.fetch_btn = QPushButton("📊 获取战绩")
        self.fetch_btn.clicked.connect(self.start_fetching)
        self.fetch_btn.setEnabled(False)
        
        self.save_btn = QPushButton("💾 保存数据")
        self.save_btn.clicked.connect(self.save_data)
        self.save_btn.setEnabled(False)
        
        self.auto_accept_btn = QPushButton("🎮 自动接受")
        self.auto_accept_btn.setCheckable(True)
        self.auto_accept_btn.clicked.connect(self.toggle_auto_accept)
        self.auto_accept_btn.setEnabled(False)
        
        self.exit_btn = QPushButton("❌ 退出")
        self.exit_btn.clicked.connect(self.close)
        
        button_layout.addWidget(self.fetch_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.auto_accept_btn)
        button_layout.addWidget(self.exit_btn)
        
        button_group.setLayout(button_layout)
        main_layout.addWidget(button_group)
        
        # 进度显示
        progress_group = QGroupBox("进度")
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(10)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        self.progress_label = QLabel("准备就绪")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.auto_accept_status = QLabel("")
        self.auto_accept_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.auto_accept_status)
        
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        # 结果显示
        result_group = QGroupBox("比赛记录")
        result_layout = QVBoxLayout()
        result_layout.setSpacing(10)
        
        self.result_tabs = QTabWidget()
        self.result_display = QTextBrowser()
        self.result_display.setReadOnly(True)
        self.result_display.setOpenLinks(False)
        self.result_display.anchorClicked.connect(self.open_champion_url)
        
        self.result_tabs.addTab(self.result_display, "战绩")
        result_layout.addWidget(self.result_tabs)
        
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

    def select_champion(self):
        """根据用户选择自动选择英雄"""
        if not self.auth_token or not self.app_port:
            QMessageBox.warning(self, "错误", "请先获取认证令牌和端口")
            return
        # 获取用户选择的中文英雄名
        selected_hero_zh = self.hero_combo.currentText()
        champion_id = CHAMPION_ZH_TO_ID.get(selected_hero_zh)
        if not champion_id:
            QMessageBox.warning(self, "错误", f"未找到英雄: {selected_hero_zh}")
            return
        # 获取当前用户所在的行动ID
        session_url = f"https://riot:{self.auth_token}@127.0.0.1:{self.app_port}/lol-champ-select/v1/session"
        try:
            session_response = requests.get(
                session_url,
                auth=HTTPBasicAuth('riot', self.auth_token),
                verify=False,
                timeout=5
            )
            if session_response.status_code == 200:
                session_data = session_response.json()
                action_id = self.find_user_action_id(session_data)
                if action_id:
                    # 检查是否为自动选择
                    #hasattr(self, 'auto_select_btn') and
                    if  self.auto_select_btn.isChecked():
                        # 自动选择英雄
                        action_url = f"https://riot:{self.auth_token}@127.0.0.1:{self.app_port}/lol-champ-select/v1/session/actions/{action_id}"
                        response = requests.patch(
                            action_url,
                            json={
                                "championId": champion_id,
                                "completed": True,
                            },
                            auth=HTTPBasicAuth('riot', self.auth_token),
                            verify=False,
                            timeout=10
                        )
                        if response.status_code == 204:
                            self.status_bar.showMessage(f"已自动选择英雄: {selected_hero_zh}")
                        else:
                            self.status_bar.showMessage(f"自动选择英雄失败: {response.status_code}")
                        return
                    # 手动选择逻辑
                    action_url = f"https://riot:{self.auth_token}@127.0.0.1:{self.app_port}/lol-champ-select/v1/session/actions/{action_id}"
                    response = requests.patch(
                        action_url,
                        json={
                            "championId": champion_id,
                            "completed": True,
                        },
                        auth=HTTPBasicAuth('riot', self.auth_token),
                        verify=False,
                        timeout=10
                    )
                    if response.status_code == 204:
                        self.status_bar.showMessage(f"已选择英雄: {selected_hero_zh}")
                    else:
                        self.status_bar.showMessage(f"选择英雄失败: {response.status_code}")
                else:
                    self.status_bar.showMessage("未找到用户行动ID")
            else:
                self.status_bar.showMessage(f"获取会话失败: {session_response.status_code}")
        except Exception as e:
            self.status_bar.showMessage(f"选择英雄出错: {str(e)}")
            
    def find_user_action_id(self, session_data):
        """在会话数据中查找用户的行动ID"""
        # 获取当前用户的cellId
        local_player_cell_id = session_data.get('localPlayerCellId')
        
        # 遍历所有回合的行动
        for round_actions in session_data.get('actions', []):
            for action in round_actions:
                if action.get('actorCellId') == local_player_cell_id and not action.get('completed'):
                    return action.get('id')
        return None

        
    def toggle_auto_accept(self, checked):
        """切换自动接受功能"""
        if checked:
            if not self.auth_token or not self.app_port:
                QMessageBox.warning(self, "错误", "请先获取认证令牌和端口")
                self.auto_accept_btn.setChecked(False)
                return
            
            # 启动自动接受线程
            self.auto_accept_thread = AutoAcceptThread(self.auth_token, self.app_port)
            self.auto_accept_thread.status_signal.connect(self.update_auto_accept_status)
            self.auto_accept_thread.teammate_signal.connect(self.on_teammates_found)
            self.auto_accept_thread.start()
            self.auto_accept_status.setText("自动接受已开启")
        else:
            # 停止自动接受线程
            if self.auto_accept_thread:
                self.auto_accept_thread.stop()
                self.auto_accept_thread = None
            self.auto_accept_status.setText("自动接受已关闭")



    def update_auto_accept_status(self, message):
        """更新自动接受状态"""
        self.auto_accept_status.setText(message)

    def on_teammates_found(self, teammate_puuids):
        """处理找到的队友信息"""
        # 检测到队友后自动选择英雄
        if hasattr(self, 'auto_select_btn') and self.auto_select_btn.isChecked():
            self.select_champion()
        # 清理旧的标签页
        while self.result_tabs.count() > 1:  # 保留第一个"我的战绩"标签
            self.result_tabs.removeTab(1)
        # 显示基本信息
        base_info = "<h3>当前队友：</h3>"
        for teammate in teammate_puuids:
            name = teammate['gameName']
            tag = teammate['tagLine']
            base_info += f"<p><b>{name}#{tag}</b></p>"
        self.result_display.setHtml(base_info)
        # 为每个队友创建新的标签页并开始获取战绩
        for teammate in teammate_puuids:
            # 创建新的文本显示区域
            teammate_display = QTextBrowser()
            teammate_display.setReadOnly(True)
            teammate_display.setStyleSheet("background-color: #f8f9fa;")
            teammate_display.setOpenLinks(False)
            teammate_display.anchorClicked.connect(self.open_champion_url)
            # 添加新标签页
            tab_name = f"{teammate['gameName']}#{teammate['tagLine']}"
            self.result_tabs.addTab(teammate_display, tab_name)
            # 启动工作线程获取战绩
            worker = TeammateWorkerThread(
                self.auth_token,
                self.app_port,
                teammate['puuid'],
                teammate['gameName'],
                teammate['tagLine']
            )
            # 保存引用避免垃圾回收
            if not hasattr(self, 'teammate_workers'):
                self.teammate_workers = []
            self.teammate_workers.append(worker)
            # 连接信号
            worker.result.connect(self.on_teammate_result)
            worker.error.connect(self.show_error)
            worker.progress.connect(self.update_progress)
            # 开始获取战绩
            worker.start()

    def on_teammate_result(self, match_history, puuid, game_name, tag_line):
        """处理队友战绩结果"""
        # 查找对应的标签页
        tab_name = f"{game_name}#{tag_line}"
        for i in range(self.result_tabs.count()):
            if self.result_tabs.tabText(i) == tab_name:
                text_browser = self.result_tabs.widget(i)
                
                # 准备显示数据
                self._games_for_img = match_history.get('games', {}).get('games', [])[:20]
                self._result_html_args = (self._games_for_img, match_history.get('totalCount', 0))
                
                # 收集英雄图标
                champion_names = set()
                for game in self._games_for_img:
                    for participant in game.get('participants', []):
                        if participant.get('puuid') == puuid:
                            champion_id = participant.get('championId')
                            champion_en = CHAMPION_MAP.get(champion_id, f"Unknown_{champion_id}")
                            champion_names.add(champion_en)
                            break
                
                # 启动图片下载线程
                self.img_thread = ImageDownloaderThread(champion_names)
                self.img_thread.finished.connect(lambda img_map: self._refresh_teammate_result_html(
                    text_browser, game_name, tag_line, img_map
                ))
                self.img_thread.start()
                break

    def _refresh_teammate_result_html(self, text_browser, game_name, tag_line, img_map=None):
        """刷新队友战绩显示"""
        games, total_count = self._games_for_img, self._result_html_args[1]
        result_text = f"<h2>比赛记录 - {game_name}#{tag_line}</h2>"
        
        if total_count >= 0 and games:
            total_kills = total_deaths = total_assists = wins = losses = 0
            
            # 统计数据
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
                    
            # 计算平均值
            avg_kills = total_kills / len(games) if games else 0
            avg_deaths = total_deaths / len(games) if games else 0
            avg_assists = total_assists / len(games) if games else 0
            avg_kda = (total_kills + total_assists) / total_deaths if total_deaths > 0 else 0
            win_rate = wins / len(games) * 100 if games else 0
            
            # 显示统计信息
            result_text += f"<div style='background-color:#f0f8ff; padding:10px; border-radius:5px; margin-bottom:15px;'>"
            result_text += f"<h3>最近{len(games)}场比赛统计</h3>"
            result_text += f"<p><b>胜率:</b> {wins}胜{losses}负 ({win_rate:.1f}%)</p>"
            result_text += f"<p><b>平均KDA:</b> {avg_kda:.1f} ({avg_kills:.1f}/{avg_deaths:.1f}/{avg_assists:.1f})</p>"
            result_text += "</div>"
            
            # 显示最近比赛
            result_text += f"<p><b>最近比赛详情:</b></p>"
            for i, game in enumerate(games[:20], 1):  # 只显示最近5场
                result_text += self._generate_game_html(game, i, img_map)
                
        text_browser.setHtml(result_text)

    def _generate_game_html(self, game, index, img_map):
        """生成单场比赛的HTML"""
        html = f"<hr><h3>比赛 #{index}</h3>"
        html += f"<p><b>模式:</b> {game.get('gameMode', '未知模式')}</p>"
        
        # 添加时间信息
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
        html += f"<p><b>开始时间:</b> {display_time}</p>"
        
        # 添加比赛时长
        duration = game.get('gameDuration', 0)
        minutes, seconds = divmod(duration, 60)
        html += f"<p><b>持续时间:</b> {minutes}分{seconds}秒</p>"
        
        # 添加英雄和战绩信息
        for participant in game.get('participants', []):
            champion_id = participant.get('championId')
            champion_en = CHAMPION_MAP.get(champion_id, f"Unknown_{champion_id}")
            stats = participant.get('stats', {})
            
            # 处理英雄图标
            if img_map and champion_en in img_map:
                img_src = img_map[champion_en]
                if os.path.exists(img_src):
                    img_src = 'file:///' + img_src.replace('\\', '/')
            else:
                img_src = f"https://ddragon.leagueoflegends.com/cdn/14.13.1/img/champion/{champion_en}.png"
                
            html += f"<p><b>英雄:</b> <img src='{img_src}' width='48' height='48' style='vertical-align:middle;margin-right:8px;'> {champion_en}</p>"
            html += f"<p><b>KDA:</b> {stats.get('kills', 0)}/{stats.get('deaths', 0)}/{stats.get('assists', 0)}</p>"
            
            win_color = "green" if stats.get('win', False) else "red"
            html += f"<p><b>结果:</b> <span style='color:{win_color};font-weight:bold;'>"
            html += "胜利" if stats.get('win', False) else "失败"
            html += "</span></p>"
            break
            
        return html

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
                #self.fetch_team_btn.setEnabled(True)
                self.auto_accept_btn.setEnabled(True)  # 启用自动接受按钮
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
        # 停止自动接受线程
        if self.auto_accept_thread:
            self.auto_accept_thread.stop()
            self.auto_accept_thread.wait()
        
        # 清理临时文件
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

    def filter_heroes(self, text):
        """根据搜索文本过滤选择英雄下拉框"""
        current_text = self.hero_combo.currentText()
        self.hero_combo.clear()
        heroes = sorted(CHAMPION_ZH_TO_ID.keys())
        filtered = [hero for hero in heroes if text.lower() in hero.lower()]
        self.hero_combo.addItems(filtered)
        # 尝试恢复之前的选择
        if current_text in filtered:
            self.hero_combo.setCurrentText(current_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 下载并设置应用图标
    icon_path = download_app_icon()
    if icon_path:
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
        
        # 设置Windows任务栏图标
        # if os.name == 'nt':  # Windows系统
        myappid = 'ByteFlowing.LOLMatchHistory.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    # 设置应用样式
    app.setStyleSheet("""
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
    """)
    
    window = LOLMatchHistoryApp()
    window.show()
    sys.exit(app.exec_())