# 日志目录路径
LOG_DIR = r"C:\WeGameApps\英雄联盟\LeagueClient"

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