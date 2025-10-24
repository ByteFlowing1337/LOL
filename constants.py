import winreg
import os

# --- LCU 根路径查找函数 ---

# 日志目录路径
def find_league_client_root_static():
    """
    尝试通过注册表查找英雄联盟客户端的安装根目录 (LeagueClient 文件夹)。
    查找失败时，尝试通用路径作为后备。
    """
    # 注册表路径（适用于 Riot Client 安装）
    REG_KEY_PATH = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Riot Game league_of_legends.live"
    
    # 尝试从注册表读取路径
    try:
        # 使用 KEY_WOW64_64KEY 确保在 64 位系统上找到 64 位应用程序的键
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_KEY_PATH, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        # 查找名为 'InstallLocation' 的值，例如: C:\Riot Games\League of Legends
        install_location, _ = winreg.QueryValueEx(key, "InstallLocation")
        winreg.CloseKey(key)
        
        # 检查路径是否有效
        if os.path.isdir(install_location):
            # LCU 日志位于此根目录的 Logs/LeagueClient Logs 子目录中
            # 但 Riot Games 的根目录通常是 LOL 文件夹。我们需要找到最终的 LeagueClient 文件夹。
            # 对于 Riot Games 安装，根目录可能已经是 C:\Riot Games\League of Legends，
            # WeGame 安装则可能是 C:\WeGameApps\英雄联盟\LeagueClient
            
            # 简单返回注册表中的路径，通常是客户端的根目录
            return install_location 
            
    except FileNotFoundError:
        pass 
    except Exception:
        pass 

    # 2. 后备方案：尝试常见的默认路径
    common_paths = [
        r"C:\Riot Games\League of Legends", # Riot Games 默认路径
        r"D:\Riot Games\League of Legends",
        r"C:\WeGameApps\英雄联盟\LeagueClient" # WeGame 默认路径
    ]
    
    for path in common_paths:
        if os.path.isdir(path):
            return path
            
    # 3. 彻底失败
    return None

# ----------------------------------------------------
# 2. 定义两个全局常量
# ----------------------------------------------------

# CLIENT_ROOT_PATH: LeagueClient 的根目录 (你想要的结果)
CLIENT_ROOT_PATH = find_league_client_root_static()

if CLIENT_ROOT_PATH:
    # LOG_DIR: LCU 日志文件的精确目录 (lcu_api.py 需要的结果)
    LOG_DIR = os.path.join(CLIENT_ROOT_PATH)
else:
    # 如果找不到根目录，将 LOG_DIR 设置为 None
    LOG_DIR = "C:\\WeGameApps\\英雄联盟\\LeagueClient"

# 英雄ID到名称的映射 (基于 Data Dragon CDN 15.21.1)
CHAMPION_MAP = {
    1: "Annie", 2: "Olaf", 3: "Galio", 4: "TwistedFate", 5: "XinZhao", 6: "Urgot", 7: "Leblanc", 8: "Vladimir", 9: "Fiddlesticks", 10: "Kayle",
    11: "MasterYi", 12: "Alistar", 13: "Ryze", 14: "Sion", 15: "Sivir", 16: "Soraka", 17: "Teemo", 18: "Tristana", 19: "Warwick", 20: "Nunu",
    21: "MissFortune", 22: "Ashe", 23: "Tryndamere", 24: "Jax", 25: "Morgana", 26: "Zilean", 27: "Singed", 28: "Evelynn", 29: "Twitch", 30: "Karthus",
    31: "Chogath", 32: "Amumu", 33: "Rammus", 34: "Anivia", 35: "Shaco", 36: "DrMundo", 37: "Sona", 38: "Kassadin", 39: "Irelia", 40: "Janna",
    41: "Gangplank", 42: "Corki", 43: "Karma", 44: "Taric", 45: "Veigar", 48: "Trundle", 50: "Swain", 51: "Caitlyn", 53: "Blitzcrank", 54: "Malphite",
    55: "Katarina", 56: "Nocturne", 57: "Maokai", 58: "Renekton", 59: "JarvanIV", 60: "Elise", 61: "Orianna", 62: "MonkeyKing", 63: "Brand", 64: "LeeSin",
    67: "Vayne", 68: "Rumble", 69: "Cassiopeia", 72: "Skarner", 74: "Heimerdinger", 75: "Nasus", 76: "Nidalee", 77: "Udyr", 78: "Poppy", 79: "Gragas",
    80: "Pantheon", 81: "Ezreal", 82: "Mordekaiser", 83: "Yorick", 84: "Akali", 85: "Kennen", 86: "Garen", 89: "Leona", 90: "Malzahar", 91: "Talon",
    92: "Riven", 96: "KogMaw", 98: "Shen", 99: "Lux", 101: "Xerath", 102: "Shyvana", 103: "Ahri", 104: "Graves", 105: "Fizz", 106: "Volibear",
    107: "Rengar", 110: "Varus", 111: "Nautilus", 112: "Viktor", 113: "Sejuani", 114: "Fiora", 115: "Ziggs", 117: "Lulu", 119: "Draven", 120: "Hecarim",
    121: "Khazix", 122: "Darius", 126: "Jayce", 127: "Lissandra", 131: "Diana", 133: "Quinn", 134: "Syndra", 136: "AurelionSol", 141: "Kayn", 142: "Zoe",
    143: "Zyra", 145: "Kaisa", 147: "Seraphine", 150: "Gnar", 154: "Zac", 157: "Yasuo", 161: "Velkoz", 163: "Taliyah", 164: "Camille", 166: "Akshan",
    200: "Belveth", 201: "Braum", 202: "Jhin", 203: "Kindred", 221: "Zeri", 222: "Jinx", 223: "TahmKench", 233: "Briar", 234: "Viego", 235: "Senna",
    236: "Lucian", 238: "Zed", 240: "Kled", 245: "Ekko", 246: "Qiyana", 254: "Vi", 266: "Aatrox", 267: "Nami", 268: "Azir", 350: "Yuumi",
    360: "Samira", 412: "Thresh", 420: "Illaoi", 421: "RekSai", 427: "Ivern", 429: "Kalista", 432: "Bard", 497: "Rakan", 498: "Xayah", 516: "Ornn",
    517: "Sylas", 518: "Neeko", 523: "Aphelios", 526: "Rell", 555: "Pyke", 711: "Vex", 777: "Yone", 799: "Ambessa", 800: "Mel", 804: "Yunara",
    875: "Sett", 876: "Lillia", 887: "Gwen", 888: "Renata", 893: "Aurora", 895: "Nilah", 897: "KSante", 901: "Smolder", 902: "Milio", 910: "Hwei", 950: "Naafiri"
}

# CHAMPION_ZH_MAP = {
#     "Aatrox": "亚托克斯", "Ahri": "阿狸", "Akali": "阿卡丽", "Akshan": "阿克尚", "Alistar": "阿利斯塔",
#     "Ambessa": "安蓓萨", "Amumu": "阿木木", "Anivia": "艾尼维亚", "Annie": "安妮", "Aphelios": "厄斐琉斯",
#     "Ashe": "艾希", "Aurelion Sol": "奥瑞利安·索尔", "Aurora": "奥罗拉", "Azir": "阿兹尔", "Bard": "巴德",
#     "Bel'Veth": "卑尔维斯", "Blitzcrank": "布里茨", "Brand": "布兰德", "Braum": "布隆", "Briar": "百裂冥犬",
#     "Caitlyn": "凯特琳", "Camille": "卡蜜尔", "Cassiopeia": "卡西奥佩娅", "Cho'Gath": "科加斯", "Corki": "库奇",
#     "Darius": "德莱厄斯", "Diana": "黛安娜", "Draven": "德莱文", "Dr. Mundo": "蒙多医生", "Ekko": "艾克",
#     "Elise": "伊莉丝", "Evelynn": "伊芙琳", "Ezreal": "伊泽瑞尔", "Fiddlesticks": "费德提克", "Fiora": "菲奥娜",
#     "Fizz": "菲兹", "Galio": "加里奥", "Gangplank": "普朗克", "Garen": "盖伦", "Gnar": "纳尔", "Gragas": "古拉加斯",
#     "Graves": "格雷福斯", "Gwen": "格温", "Hecarim": "赫卡里姆", "Heimerdinger": "黑默丁格", "Hwei": "彗",
#     "Illaoi": "俄洛伊", "Irelia": "艾瑞莉娅", "Ivern": "艾翁", "Janna": "迦娜", "Jarvan IV": "嘉文四世",
#     "Jax": "贾克斯", "Jayce": "杰斯", "Jhin": "烬", "Jinx": "金克丝", "Kai'Sa": "卡莎", "Kalista": "卡莉丝塔",
#     "Karma": "卡尔玛", "Karthus": "卡尔萨斯", "Kassadin": "卡萨丁", "Katarina": "卡特琳娜", "Kayle": "凯尔",
#     "Kayn": "凯隐", "Kennen": "凯南", "Kha'Zix": "卡兹克", "Kindred": "千珏", "Kled": "克烈", "Kog'Maw": "克格莫",
#     "K'Sante": "奎桑提", "LeBlanc": "乐芙兰", "Lee Sin": "李青", "Leona": "蕾欧娜", "Lillia": "莉莉娅",
#     "Lissandra": "丽桑卓", "Lucian": "卢锡安", "Lulu": "璐璐", "Lux": "拉克丝", "Malphite": "墨菲特",
#     "Malzahar": "玛尔扎哈", "Maokai": "茂凯", "Master Yi": "易", "Mel": "梅尔", "Milio": "米利欧",
#     "MissFortune": "厄运小姐", "Wukong": "孙悟空", "Mordekaiser": "莫德凯撒", "Morgana": "莫甘娜", "Naafiri": "纳亚菲利",
#     "Nami": "娜美", "Nasus": "内瑟斯", "Nautilus": "诺提勒斯", "Neeko": "妮蔻", "Nidalee": "奈德丽", "Nilah": "尼菈",
#     "Nocturne": "魔腾", "Nunu & Willump": "努努和威朗普", "Olaf": "奥拉夫", "Orianna": "奥莉安娜", "Ornn": "奥恩",
#     "Pantheon": "潘森", "Poppy": "波比", "Pyke": "派克", "Qiyana": "奇亚娜", "Quinn": "奎因", "Rakan": "洛",
#     "Rammus": "拉莫斯", "Rek'Sai": "雷克塞", "Rell": "芮尔", "Renata Glasc": "烈娜塔", "Renekton": "雷克顿",
#     "Rengar": "雷恩加尔", "Riven": "锐雯", "Rumble": "兰博", "Ryze": "瑞兹", "Samira": "莎弥拉", "Sejuani": "瑟庄妮",
#     "Senna": "赛娜", "Seraphine": "萨勒芬妮", "Sett": "瑟提", "Shaco": "萨科", "Shen": "慎", "Shyvana": "希瓦娜",
#     "Singed": "辛吉德", "Sion": "赛恩", "Sivir": "希维尔", "Skarner": "斯卡纳", "Smolder": "斯莫德", "Sona": "娑娜",
#     "Soraka": "索拉卡", "Swain": "斯维因", "Sylas": "塞拉斯", "Syndra": "辛德拉", "Tahm Kench": "塔姆",
#     "Taliyah": "塔莉垭", "Talon": "泰隆", "Taric": "塔里克", "Teemo": "提莫", "Thresh": "锤石", "Tristana": "崔丝塔娜",
#     "Trundle": "特朗德尔", "Tryndamere": "泰达米尔", "Twisted Fate": "崔斯特", "Twitch": "图奇", "Udyr": "乌迪尔",
#     "Urgot": "厄加特", "Varus": "韦鲁斯", "Vayne": "薇恩", "Veigar": "维迦", "Vel'Koz": "维克兹", "Vex": "薇古丝",
#     "Vi": "蔚", "Viego": "佛耶戈", "Viktor": "维克托", "Vladimir": "弗拉基米尔", "Volibear": "沃利贝尔",
#     "Warwick": "沃里克", "Xayah": "霞", "Xerath": "泽拉斯", "XinZhao": "赵信", "Yasuo": "亚索", "Yone": "永恩",
#     "Yorick": "约里克", "Yuumi": "悠米", "Zac": "扎克", "Zed": "劫", "Zeri": "泽丽", "Ziggs": "吉格斯",
#     "Zilean": "基兰", "Zoe": "佐伊", "Zyra": "婕拉"
# }

# CHAMPION_ZH_TO_ID = {
#     CHAMPION_ZH_MAP.get(en_name, en_name): id
#     for id, en_name in CHAMPION_MAP.items()
# }
    
