"""
API路由模块
处理HTTP请求
"""
from flask import Blueprint, render_template, jsonify, request
from config import app_state
from constants import CHAMPION_MAP
from core import lcu
from core.lcu.enrichment import enrich_game_with_augments
from utils.game_data_formatter import format_game_data
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# OP.GG integration has been removed from this build.
OPGG_AVAILABLE = False

# 创建蓝图
api_bp = Blueprint('api', __name__)

# 向后兼容的别名
api = api_bp


@api_bp.route('/')
def index():
    """渲染主页面"""
    return render_template('index.html')


@api_bp.route('/summoner/<path:summoner_name>')
def summoner_detail(summoner_name):
    """
    渲染召唤师详细战绩页面
    
    Args:
        summoner_name: 召唤师名称 (格式: 名称#TAG)
    
    Returns:
        HTML: 详细战绩页面
    """
    # allow optional puuid query param to bypass name->puuid lookup in the client
    puuid = request.args.get('puuid')
    # pass champion map so templates can resolve championId -> champion key for ddragon
    return render_template('summoner_detail.html', summoner_name=summoner_name, champion_map=CHAMPION_MAP, puuid=puuid)


@api_bp.route('/match/<path:summoner_name>/<int:game_index>')
def match_detail_page(summoner_name, game_index):
    """渲染单场对局详情页面（前端将调用 /get_match 获取具体数据）"""
    # pass champion map so the template can resolve championId -> champion key
    return render_template('match_detail.html', summoner_name=summoner_name, game_index=game_index, champion_map=CHAMPION_MAP)


@api_bp.route('/live_game')
def live_game():
    """
    渲染实时游戏监控页面
    
    Returns:
        HTML: 实时游戏详情页面
    """
    return render_template('live_game.html')





@api_bp.route('/get_history', methods=['GET'])
def get_history():
    """
    获取指定召唤师的战绩
    
    查询参数:
        name: 召唤师名称 (格式: 名称#TAG)
    
    Returns:
        JSON: 包含战绩数据的响应
    """
    # support either name OR puuid to speed up lookups from client
    summoner_name = request.args.get('name')
    puuid = request.args.get('puuid')

    if not summoner_name and not puuid:
        return jsonify({
            "success": False,
            "message": "请求缺少召唤师名称 (name) 或 puuid 查询参数"
        })

    if not app_state.is_lcu_connected():
        return jsonify({
            "success": False,
            "message": "未连接到客户端"
        })

    # 获取PUUID（若客户端未直接提供）
    token = app_state.lcu_credentials["auth_token"]
    port = app_state.lcu_credentials["app_port"]
    if not puuid:
        puuid = lcu.get_puuid(token, port, summoner_name)
        if not puuid:
            return jsonify({
                "success": False,
                "message": f"找不到召唤师 '{summoner_name}' 或 LCU API 失败"
            })

    # 🚀 优化：默认只查询 20 场（页面只显示20场），支持自定义查询数量
    # 用户如果需要更多历史记录，可以通过 count 参数指定（最多200场）
    count = request.args.get('count', 20, type=int)  # 默认从100改为20
    count = min(max(count, 1), 200)  # 限制在1-200之间
    
    # 获取战绩
    history = lcu.get_match_history(token, port, puuid, count=count)
    if not history:
        return jsonify({
            "success": False,
            "message": "获取战绩失败"
        })
    
    # 处理数据
    processed_games = _process_match_history(history)
    
    # OP.GG integration removed: processed_games contains core match info only.
    
    return jsonify({
        "success": True, 
        "games": processed_games
    })


@api_bp.route('/get_match', methods=['GET'])
def get_match():
    """
    返回指定召唤师历史列表中某一场的完整对局信息（包含所有参赛者）

    查询参数:
        name: 召唤师名称 (格式: 名称#TAG)
        index: 在 /get_history 返回的 games 列表中的索引 (整数，0 表示最近一场)
    """
    summoner_name = request.args.get('name')
    index = request.args.get('index', type=int)

    # support fetching by match_id directly
    match_id = request.args.get('match_id')

    if match_id:
        if not app_state.is_lcu_connected():
            return jsonify({"success": False, "message": "未连接到客户端"}), 400
        token = app_state.lcu_credentials["auth_token"]
        port = app_state.lcu_credentials["app_port"]
        match_obj = lcu.get_match_by_id(token, port, match_id)
        if match_obj:
            # Some LCU endpoints return a wrapper with a nested 'game' object.
            # Normalize so we always return the inner game dict and run enrichment
            # to fill missing summonerName / profileIcon before returning.
            game = match_obj.get('game') if (isinstance(match_obj, dict) and 'game' in match_obj) else match_obj
            try:
                lcu.enrich_game_with_summoner_info(token, port, game)
                enrich_game_with_augments(game)  # 添加 augment 图标 URL
            except Exception as e:
                print(f"召唤师信息补全失败 (match_id path): {e}")
            return jsonify({"success": True, "game": game})
        else:
            return jsonify({"success": False, "message": "通过 match_id 获取对局失败"}), 404

    if not summoner_name or index is None:
        return jsonify({"success": False, "message": "缺少参数 name 或 index"}), 400

    if not app_state.is_lcu_connected():
        return jsonify({"success": False, "message": "未连接到客户端"}), 400

    token = app_state.lcu_credentials["auth_token"]
    port = app_state.lcu_credentials["app_port"]
    puuid = lcu.get_puuid(token, port, summoner_name)
    if not puuid:
        return jsonify({"success": False, "message": f"找不到召唤师 '{summoner_name}' 或 LCU API 失败"}), 404

    # 🚀 优化：只查询必要的战绩数量（index+10场作为缓冲）
    # 如果 index=0，查询20场；index=10，查询30场，以此类推
    fetch_count = min(index + 20, 200)  # 最多200场
    history = lcu.get_match_history(token, port, puuid, count=fetch_count)
    if not history:
        return jsonify({"success": False, "message": "获取战绩失败"}), 500

    games = history.get('games', {}).get('games', [])
    if index < 0 or index >= len(games):
        return jsonify({"success": False, "message": "索引越界"}), 400

    game = games[index]

    # 尝试使用 LCU API 补全参与者的召唤师名和头像（如果返回数据缺失）
    try:
        lcu_token = token
        lcu_port = port
        lcu.enrich_game_with_summoner_info(lcu_token, lcu_port, game)
        enrich_game_with_augments(game)  # 添加 augment 图标 URL
    except Exception as e:
        # enrichment 是 best-effort，不应阻塞主响应
        print(f"召唤师信息补全失败: {e}")

    # 返回完整对局对象（尽量保持原始结构，前端负责格式化展示）
    return jsonify({"success": True, "game": game})


# OP.GG helper removed.


@api_bp.route('/get_live_game_data', methods=['GET'])
def get_live_game_data():
    """
    获取实时游戏数据（从游戏API 2999端口）
    
    Returns:
        JSON: 格式化后的游戏数据（队友、敌人、游戏信息等）
    """
    try:
        # 尝试连接游戏客户端API（端口2999，减少timeout）
        response = requests.get('https://127.0.0.1:2999/liveclientdata/allgamedata', 
                               verify=False, timeout=2)
        
        if response.status_code == 200:
            all_game_data = response.json()
            formatted_data = format_game_data(all_game_data)
            
            # OP.GG integration removed: returning formatted game data without external stats.
            
            return jsonify({
                "success": True,
                "inGame": True,
                "data": formatted_data
            })
        else:
            return jsonify({
                "success": False,
                "inGame": False,
                "message": "无法连接到游戏客户端"
            })
            
    except requests.exceptions.RequestException:
        return jsonify({
            "success": False,
            "inGame": False,
            "message": "未在游戏中或游戏API不可用"
        })


def _process_match_history(history):
    """
    处理战绩数据，提取关键信息
    
    Args:
        history: LCU API返回的原始战绩数据
    
    Returns:
        list: 处理后的战绩列表
    """
    processed_games = []
    games = history.get('games', {}).get('games', [])[:20]  # 取最近20场
    
    for idx, game in enumerate(games):
        participant = game['participants'][0]
        champion_en = CHAMPION_MAP.get(participant['championId'], 'Unknown')
        stats = participant['stats']
        
        # 计算时间差
        game_creation = game.get('gameCreation', 0)
        time_diff = _calculate_time_ago(game_creation)
        
        # 提取金币和CS
        gold_earned = stats.get('goldEarned', 0)
        total_cs = stats.get('totalMinionsKilled', 0) + stats.get('neutralMinionsKilled', 0)
        
        # try to extract a stable match id from the game object (varies by LCU/Riot versions)
        match_id = None
        if isinstance(game, dict):
            match_id = game.get('matchId') or game.get('gameId') or game.get('id') or (game.get('metadata') or {}).get('matchId')

        # CHERRY 模式：提取子队伍排名信息
        subteam_placement = None
        if game.get('gameMode') == 'CHERRY':
            subteam_placement = stats.get('subteamPlacement', 0)

        # keep a lightweight identifier (index) so frontend can request full match later
        processed_games.append({
            "champion_en": champion_en,
            "kda": f"{stats['kills']}/{stats['deaths']}/{stats['assists']}",
            "win": stats['win'],
            "gameMode": game.get('gameMode', 'UNKNOWN'),
            "mode": _format_game_mode(game.get('gameMode', '')),
            "gold": f"{gold_earned:,}",
            "cs": total_cs,
            "time_ago": time_diff,
            "duration": game.get('gameDuration', 0),
            "subteamPlacement": subteam_placement,  # CHERRY 模式排名
            # index into the returned games list (0 = most recent)
            "match_index": idx,
            # preserve creation timestamp to help identification
            "game_creation": game.get('gameCreation'),
            # include match_id when present so front-end can request full match by id
            "match_id": match_id
        })
    
    return processed_games


def _format_game_mode(mode):
    """格式化游戏模式名称"""
    mode_map = {
        'CLASSIC': '经典模式',
        'ARAM': '极地大乱斗',
        'KIWI': '大乱斗',
        'CHERRY': '斗魂竞技场',
        'URF': '无限火力',
        'ONEFORALL': '克隆模式',
        'NEXUSBLITZ': '激斗峡谷',
        'TUTORIAL': '教程',
        'PRACTICETOOL': '训练模式'
    }
    return mode_map.get(mode, mode)


def _calculate_time_ago(timestamp_ms):
    """计算时间差"""
    from datetime import datetime
    
    if not timestamp_ms:
        return '未知时间'
    
    game_time = datetime.fromtimestamp(timestamp_ms / 1000)
    now = datetime.now()
    diff = now - game_time
    
    if diff.days > 0:
        return f"{diff.days}天前"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours}小时前"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes}分钟前"
    else:
        return "刚刚"
