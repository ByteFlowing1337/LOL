import os
import re
import requests
from requests.auth import HTTPBasicAuth # 确保导入 HTTPBasicAuth，用于 LCU 认证
import json
#import datetime
import chardet
import psutil
from constants import LOG_DIR 
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 辅助函数：文件操作和凭证提取 ---

def is_league_client_running(status_bar):
    """
    检测 LeagueClient.exe 进程是否正在运行。
    """
    client_process_name = "LeagueClientUx.exe" 
    
    # 遍历所有正在运行的进程
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == client_process_name:
            status_bar.showMessage(f"✅ 检测到进程: {client_process_name} 正在运行。")
            return True
            
    status_bar.showMessage(f"❌ 未检测到进程: {client_process_name}。请先启动客户端。")
    return False

def detect_file_encoding(file_path, status_bar):
    """检测文件编码，现在是独立函数。"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(4096)
            result = chardet.detect(raw_data)
            return result['encoding'] or 'gbk'
    except Exception as e:
        status_bar.showMessage(f"检测文件编码失败: {e}, 默认使用GBK")
        return 'gbk'

def get_latest_log_file(status_bar):
    """获取最新的日志文件（按文件修改时间），现在是独立函数。"""
    try:
        if not os.path.exists(LOG_DIR):
            status_bar.showMessage(f"错误：日志目录未找到: {LOG_DIR}。请检查 LOG_DIR 变量。")
            return None
            
        full_log_files = []
        for f in os.listdir(LOG_DIR):
            if f.endswith("_LeagueClientUx.log") and "T" in f:
                full_log_files.append(os.path.join(LOG_DIR, f))
        
        if not full_log_files:
            status_bar.showMessage(f"未在目录 {LOG_DIR} 中找到符合条件的日志文件。")
            return None
        
        latest_file = max(full_log_files, key=os.path.getmtime)
        
        if os.path.getsize(latest_file) < 500:
            status_bar.showMessage(f"警告：最新日志文件 ({os.path.basename(latest_file)}) 太小，可能为空或正在写入。")
            return None 
            
        return latest_file
    
    except FileNotFoundError:
        status_bar.showMessage(f"错误：日志目录未找到: {LOG_DIR}")
        return None
    except Exception as e:
        status_bar.showMessage(f"获取日志文件时出错: {e}")
        return None

def extract_params_from_log(log_file, status_bar):
    """从日志文件中提取认证令牌和端口号，现在是独立函数。"""
    try:
        encoding = detect_file_encoding(log_file, status_bar)
        status_bar.showMessage(f"检测到文件编码: {encoding}")
        
        with open(log_file, "r", encoding=encoding, errors='replace') as f:
            content = f.read()
            
            token_match = re.search(r"--remoting-auth-token=([\w-]+)", content)
            port_match = re.search(r"--app-port=(\d+)", content)
            
            if token_match and port_match:
                token = token_match.group(1)
                port = int(port_match.group(1))
                status_bar.showMessage(f"成功提取参数：Token={token[:8]}..., Port={port}")
                return token, port
            else:
                status_bar.showMessage("在日志文件中未找到所需的 --remoting-auth-token 或 --app-port 参数。")
                return None, None
                
    except FileNotFoundError:
        status_bar.showMessage(f"错误：日志文件未找到: {log_file}")
        return None, None
    except Exception as e:
        status_bar.showMessage(f"读取日志文件时出错: {e}")
        return None, None



def autodetect_credentials(status_bar):
    """
    自动检测LCU凭证的入口函数：
    1. 检查 LeagueClientUx.exe 进程是否运行。
    2. 如果进程运行，则尝试从最新日志中提取凭证。
    """
    status_bar.showMessage("正在尝试自动检测 LCU 凭证 (进程+日志)...")
    
    # 🎯 步骤 1: 检查进程
    if not is_league_client_running(status_bar):
        status_bar.showMessage("⚠️ 进程检测失败。无法连接 LCU。")
        return None, None
        
    # 进程运行，继续读取日志
    log_file = get_latest_log_file(status_bar)
    
    if log_file:
        status_bar.showMessage(f"找到日志文件: {os.path.basename(log_file)}")
        auth_token, app_port = extract_params_from_log(log_file, status_bar)
        
        if auth_token and app_port:
            status_bar.showMessage("✅ LCU 进程和参数均自动获取成功!")
        else:
            status_bar.showMessage("⚠️ 进程运行中，但日志中未找到 LCU 凭证。")
            
        return auth_token, app_port
    else:
        status_bar.showMessage("⚠️ 进程运行中，但未找到有效的日志文件。")
        return None, None

# --- LCU API 通用请求函数 (使用 HTTPBasicAuth) ---

def make_request(method, endpoint, token, port, **kwargs):
    """
    统一的 LCU API 请求封装，处理认证和 SSL 验证。
    
    Args:
        method: HTTP方法
        endpoint: API端点
        token: 认证令牌
        port: 端口
        **kwargs: 其他请求参数（可包含自定义timeout）
    """
    url = f"https://127.0.0.1:{port}{endpoint}"
    # LCU 认证要求使用 HTTPBasicAuth，用户名是 'riot'
    auth = HTTPBasicAuth('riot', token) 
    
    print(f"--- LCU Request: {method} {endpoint} ---")
    
    # 强制将 data 参数从 json 转换回 data，因为 requests.request 不直接接受 json 参数
    # 但我们统一使用 **kwargs 传递，在下面处理
    if 'json' in kwargs:
        kwargs['data'] = json.dumps(kwargs.pop('json'))
        kwargs['headers'] = kwargs.get('headers', {})
        kwargs['headers']['Content-Type'] = 'application/json'

    # 🚀 动态timeout：如果没有指定，则使用默认值5秒
    # 大数据量查询（如战绩）会在调用时传入更大的timeout
    if 'timeout' not in kwargs:
        kwargs['timeout'] = 5

    try:
        response = requests.request(
            method,
            url,
            auth=auth,
            verify=False,  # 忽略SSL证书错误
            **kwargs
        )
        
        # 抛出 HTTPError 异常，处理 4xx/5xx 状态码
        response.raise_for_status() 

        if response.status_code == 204: # No Content
            return None
        
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        # 专门处理 HTTP 错误 (如 403 Forbidden)
        print(f"LCU API 请求失败 ({method} {endpoint}): {e.response.status_code} {e.response.reason}")
        # 打印 403 错误的详细信息
        if e.response.status_code == 403:
            print("!!! 权限拒绝 (403 Forbidden) !!! 可能原因: LCU 客户端限制或当前游戏状态不允许查询。")
            
        print(f"响应内容: {e.response.text}")
        return None
        
    except requests.exceptions.RequestException as e:
        # 处理其他请求异常（如连接超时、DNS 错误）
        print(f"LCU API 请求异常 ({method} {endpoint}): {e}")
        return None

# --- LCU API 功能函数 ---

def get_gameflow_phase(token, port):
    """获取当前游戏流程阶段"""
    return make_request("GET", "/lol-gameflow/v1/gameflow-phase", token, port)

def accept_ready_check(token, port):
    """接受排队准备检查"""
    return make_request("POST", "/lol-matchmaking/v1/ready-check/accept", token, port)

def get_champ_select_session(token, port):
    """获取选人会话数据"""
    return make_request("GET", "/lol-champ-select/v1/session", token, port)

def get_current_summoner(token, port):
    """获取当前登录召唤师的ID和名称"""
    return make_request("GET", "/lol-summoner/v1/current-summoner", token, port)

def get_puuid(token, port, summoner_name):
    """
    通过召唤师名字获取PUUID，使用 LCU API /lol-summoner/v1/summoners?name={summoner_name} 查询。
    """
    endpoint = "/lol-summoner/v1/summoners"
    
    # 关键：使用正则表达式移除 Unicode 控制字符，同时保留 # 号
    # 移除不可见的 Unicode 控制字符 (如 U+206E, U+2069 等 Bidi 字符)
    CLEANR = re.compile(r'[\u200e-\u200f\u202a-\u202e\u2066-\u2069]')
    cleaned_name = re.sub(CLEANR, '', summoner_name).strip() 

    # 使用 make_request 发送请求
    data = make_request(
        "GET",
        endpoint,
        token,
        port,
        params={'name': cleaned_name} # 使用查询参数传递清洗后的名称
    )
    
    if data:
        # Riot ID 查询返回的是一个包含 puuid 的字典
        return data.get('puuid')
    return None

def get_match_history(token, port, puuid, count=100):
    """
    通过 PUUID 获取比赛历史记录。
    
    Args:
        token: LCU认证令牌
        port: LCU端口
        puuid: 玩家PUUID
        count: 查询数量 (默认100场，最大值通常为200)
    
    Returns:
        dict: 战绩数据
    """
    # LCU API 战绩查询端点，PUUID 在路径中
    endpoint = f"/lol-match-history/v1/products/lol/{puuid}/matches"
    
    # 🚀 动态timeout：根据查询数量调整超时时间
    # 经验值：每100场约需5秒，基础5秒 + 额外时间
    timeout = 5 + (count // 50) * 3  # 50场+3秒，100场+6秒，200场+12秒
    timeout = min(timeout, 20)  # 最大20秒，避免等待过久
    
    print(f"📊 查询 {count} 场战绩，timeout={timeout}秒")
    
    # 🚀 优化：增加查询数量到100场（原来只有15场）
    # LCU API 支持的最大值通常为 200，这里设置为 100 平衡性能和数据量
    return make_request(
        "GET",
        endpoint,
        token,
        port,
        params={ 'endIndex': count},  # 查询从0到count的战绩
        timeout=timeout  # 传入动态timeout
    )

# --- 游戏内对局信息API（端口2999）---

def get_live_game_data():
    """
    通过游戏客户端本地API获取当前对局的实时数据（端口2999）。
    注意：此API仅在游戏进行中可用，不需要认证。
    返回包含所有玩家信息的字典，如果游戏未开始则返回None。
    """
    try:
        url = "https://127.0.0.1:2999/liveclientdata/allgamedata"
        response = requests.get(url, verify=False, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"获取游戏内数据失败（可能游戏未开始）: {e}")
        return None

def get_enemy_players_from_game():
    """
    从游戏内API获取敌方队伍的所有玩家信息。
    返回敌方玩家列表，每个玩家包含 summonerName 等信息。
    """
    game_data = get_live_game_data()
    if not game_data:
        return []
    
    try:
        all_players = game_data.get('allPlayers', [])
        # 获取当前玩家的队伍
        active_player = game_data.get('activePlayer', {})
        my_team = active_player.get('team', '')
        
        # 筛选出敌方玩家（队伍不同的玩家）
        enemy_players = [
            player for player in all_players 
            if player.get('team', '') != my_team
        ]
        
        print(f"找到 {len(enemy_players)} 名敌方玩家")
        return enemy_players
        
    except Exception as e:
        print(f"解析敌方玩家数据失败: {e}")
        return []

def get_all_players_from_game(token, port):
    """
    从游戏内API获取所有玩家信息，并分类为队友和敌人。
    
    规则：通过 activePlayer 的 team 字段确定己方队伍，
         然后根据 allPlayers 中每个玩家的 team 字段进行分类。
         - team 相同 → 队友
         - team 不同 → 敌人
    
    返回格式：
    {
        'teammates': [
            {
                'summonerName': '玩家名',
                'gameName': '游戏名',
                'tagLine': 'TAG',
                'puuid': 'xxx-xxx-xxx',
                'championName': '英雄名',
                'level': 等级,
                'team': 'ORDER' 或 'CHAOS'
            },
            ...
        ],
        'enemies': [ 同上格式 ]
    }
    """
    game_data = get_live_game_data()
    if not game_data:
        print("❌ 无法获取游戏数据（游戏可能未开始）")
        return None
    
    try:
        all_players = game_data.get('allPlayers', [])
        active_player = game_data.get('activePlayer', {})
        
        if len(all_players) < 10:
            print(f"⚠️ 玩家数据不完整，当前只有 {len(all_players)} 人")
            return None
        
        # 获取当前玩家的队伍 (ORDER 或 CHAOS)
        my_team = active_player.get('summonerName', '')
        my_team_side = None
        
        # 从 allPlayers 中找到当前玩家，确定队伍
        for player in all_players:
            if player.get('summonerName') == my_team:
                my_team_side = player.get('team', '')
                break
        
        if not my_team_side:
            print("⚠️ 无法确定当前玩家的队伍")
            return None
        
        print(f"🎮 当前玩家队伍: {my_team_side}")
        
        # 根据队伍分类玩家
        teammate_list = []
        enemy_list = []
        
        for player in all_players:
            summoner_name = player.get('summonerName', '未知')
            player_team = player.get('team', '')
            
            # 获取PUUID
            puuid = get_puuid(token, port, summoner_name)
            
            # 解析游戏名和标签
            if '#' in summoner_name:
                parts = summoner_name.split('#', 1)
                game_name = parts[0]
                tag_line = parts[1] if len(parts) > 1 else 'NA'
            else:
                game_name = summoner_name
                tag_line = 'NA'
            
            player_info = {
                'summonerName': summoner_name,
                'gameName': game_name,
                'tagLine': tag_line,
                'puuid': puuid,
                'championName': player.get('championName', '未知'),
                'level': player.get('level', 0),
                'team': player_team
            }
            
            # 根据队伍字段分类
            if player_team == my_team_side:
                teammate_list.append(player_info)
                print(f"👥 队友: {summoner_name} ({player.get('championName', '未知')}) [队伍: {player_team}]")
            else:
                enemy_list.append(player_info)
                print(f"💥 敌人: {summoner_name} ({player.get('championName', '未知')}) [队伍: {player_team}]")

        
        print(f"✅ 成功获取 {len(teammate_list)} 名队友 ({my_team_side}) 和 {len(enemy_list)} 名敌人")
        
        return {
            'teammates': teammate_list,
            'enemies': enemy_list
        }
        
    except Exception as e:
        print(f"❌ 解析玩家数据失败: {e}")
        return None

def get_enemy_stats(token, port):
    """
    【完整流程】获取敌方玩家的战绩信息。
    
    工作流程：
    1. 从游戏内API（端口2999）获取敌方召唤师名
    2. 通过LCU API将召唤师名转换为PUUID
    3. 使用PUUID查询每个敌方玩家的战绩
    
    返回格式：
    [
        {
            'summonerName': '玩家名',
            'puuid': 'xxx-xxx-xxx',
            'championId': '英雄名',
            'level': 等级
        },
        ...
    ]
    """
    enemy_players = get_enemy_players_from_game()
    if not enemy_players:
        print("❌ 无法获取敌方玩家信息（可能游戏未开始）")
        return []
    
    enemy_stats = []
    
    for player in enemy_players:
        summoner_name = player.get('summonerName', '未知')
        print(f"正在查询敌方玩家: {summoner_name}")
        
        # 步骤1: 获取PUUID（这样前端可以用来查询战绩）
        puuid = get_puuid(token, port, summoner_name)
        if not puuid:
            print(f"  ⚠️ 无法获取 {summoner_name} 的PUUID")
            enemy_stats.append({
                'summonerName': summoner_name,
                'puuid': None,
                'championId': player.get('championName', '未知'),
                'level': player.get('level', 0),
                'error': '无法获取PUUID'
            })
            continue
        
        print(f"  ✅ PUUID: {puuid[:20]}...")
        
        # 返回基本信息，战绩由前端异步查询（避免后端阻塞）
        enemy_stats.append({
            'summonerName': summoner_name,
            'puuid': puuid,
            'championId': player.get('championName', '未知'),
            'level': player.get('level', 0)
        })
        
   
    
    return enemy_stats

def get_champ_select_enemies(token, port):
    """
    【备用方案】从选人会话中获取敌方玩家信息。
    仅在选人阶段可用，游戏开始后此API无法使用。
    
    返回敌方玩家的召唤师ID列表。
    """
    session = get_champ_select_session(token, port)
    if not session:
        print("❌ 无法获取选人会话（可能不在选人阶段）")
        return []
    
    try:
        # 获取己方队伍ID
        my_team = session.get('myTeam', [])
        if not my_team:
            return []
        
        my_team_ids = {player['summonerId'] for player in my_team}
        
        # 获取所有队伍成员
        all_players = session.get('myTeam', []) + session.get('theirTeam', [])
        
        # 筛选出敌方玩家
        enemy_players = [
            player for player in all_players 
            if player.get('summonerId') not in my_team_ids
        ]
        
        print(f"选人阶段找到 {len(enemy_players)} 名敌方玩家")
        return enemy_players
        
    except Exception as e:
        print(f"解析选人会话失败: {e}")
        return []


def get_match_by_id(token, port, match_id):
    """
    通过 LCU 的 match history 接口按 match_id 获取完整对局对象。
    """
    # Try several known/possible internal endpoints for match detail. Different LCU
    # or packaged servers may expose different paths. Try them in order and
    # return the first successful JSON response.
    candidates = [
        f"/lol-match-history/v1/matches/{match_id}",
        f"/lol-match-history/v1/products/lol/matches/{match_id}",
        f"/lol-match-history/v1/games/{match_id}",
        f"/lol-match-history/v1/match/{match_id}",
        f"/match/v1/matches/{match_id}",
    ]

    for ep in candidates:
        try:
            print(f"尝试通过 LCU 端点获取对局: {ep}")
            res = make_request("GET", ep, token, port)
            if res:
                print(f"通过端点 {ep} 成功获取对局")
                return res
        except Exception as e:
            print(f"尝试端点 {ep} 时出现异常: {e}")

    # 如果都失败，打印日志供调试
    print(f"❌ 无法通过任何已知 LCU 端点获取 match_id={match_id}")
    return None


def get_summoner_by_id(token, port, summoner_id):
    """通过 summonerId 获取召唤师信息（尝试 LCU 本地接口）"""
    endpoint = f"/lol-summoner/v1/summoners/{summoner_id}"
    return make_request("GET", endpoint, token, port)


def get_summoner_by_puuid(token, port, puuid):
    """通过 puuid 获取召唤师信息（尝试本地 LCU 接口）"""
    endpoint = f"/lol-summoner/v1/summoners/by-puuid/{puuid}"
    return make_request("GET", endpoint, token, port)


def get_summoner_by_name(token, port, name):
    """通过召唤师名字查询（使用 ?name= 查询，LCU 返回可能是字典）"""
    endpoint = "/lol-summoner/v1/summoners"
    return make_request("GET", endpoint, token, port, params={'name': name})


def enrich_game_with_summoner_info(token, port, game):
    """
    尝试为 game['participants'] 中的每个参与者填充缺失的 summonerName / profileIcon / puuid
    该方法会就地修改 game 对象并返回它。
    """
    if not game or not isinstance(game, dict):
        return game

    participants = game.get('participants') or []
    # Build map from participantIdentities for fallback name/icon data
    idents = {}
    for ident in (game.get('participantIdentities') or []):
        pid = ident.get('participantId')
        player = ident.get('player') or {}
        if pid is not None:
            idents[pid] = player
    for p in participants:
        try:
            # skip if already has readable summonerName
            if p.get('summonerName'):
                continue

            info = None
            # try by puuid
            puuid = p.get('puuid') or (p.get('player') or {}).get('puuid')
            if puuid:
                info = get_summoner_by_puuid(token, port, puuid)

            # try by summonerId
            if not info:
                sid = p.get('summonerId') or (p.get('player') or {}).get('summonerId')
                if sid:
                    info = get_summoner_by_id(token, port, sid)

            # try by name
            if not info:
                name = p.get('summonerName') or (p.get('player') or {}).get('summonerName')
                if name:
                    info = get_summoner_by_name(token, port, name)

            if info and isinstance(info, dict):
                # normalize possible keys
                p['summonerName'] = info.get('displayName') or info.get('summonerName') or info.get('gameName') or p.get('summonerName')
                if 'profileIconId' in info:
                    p['profileIcon'] = info.get('profileIconId')
                elif 'profileIcon' in info:
                    p['profileIcon'] = info.get('profileIcon')
                if 'puuid' in info:
                    p['puuid'] = info.get('puuid')
            # fallback: use participantIdentities mapping if present
            if (not p.get('summonerName')) and p.get('participantId') and idents.get(p.get('participantId')):
                player = idents.get(p.get('participantId')) or {}
                game_name = (player.get('gameName') or player.get('summonerName')) or ''
                tag = player.get('tagLine')
                if game_name:
                    p['summonerName'] = f"{game_name}{('#'+tag) if tag else ''}"
                if player.get('profileIcon') is not None and not p.get('profileIcon'):
                    p['profileIcon'] = player.get('profileIcon')
                if player.get('puuid') and not p.get('puuid'):
                    p['puuid'] = player.get('puuid')
        except Exception as e:
            print(f"enrich participant failed: {e}")

    # also handle alternative participant structures (e.g., metadata or participants under different keys)
    return game