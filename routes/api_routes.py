"""
API路由模块
处理HTTP请求
"""
from flask import Blueprint, render_template, jsonify, request
from config import app_state
import lcu_api
from constants import CHAMPION_MAP
from utils.game_data_formatter import format_game_data
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 导入OP.GG API
try:
    from services.opgg_api import get_opgg_api, get_english_champion_name
    OPGG_AVAILABLE = True
except ImportError:
    OPGG_AVAILABLE = False
    print("⚠️ OP.GG API不可用")

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
    return render_template('summoner_detail.html', summoner_name=summoner_name)


@api_bp.route('/live_game')
def live_game():
    """
    渲染实时游戏监控页面
    
    Returns:
        HTML: 实时游戏详情页面
    """
    return render_template('live_game.html')


@api_bp.route('/vision_detection')
def vision_detection():
    """
    渲染CV视觉检测页面
    
    Returns:
        HTML: CV视觉检测页面
    """
    return render_template('vision_detection.html')


@api_bp.route('/get_history', methods=['GET'])
def get_history():
    """
    获取指定召唤师的战绩
    
    查询参数:
        name: 召唤师名称 (格式: 名称#TAG)
    
    Returns:
        JSON: 包含战绩数据的响应
    """
    summoner_name = request.args.get('name')
    
    if not summoner_name:
        return jsonify({
            "success": False, 
            "message": "请求缺少召唤师名称 (name) 查询参数"
        })

    if not app_state.is_lcu_connected():
        return jsonify({
            "success": False, 
            "message": "未连接到客户端"
        })

    # 获取PUUID
    token = app_state.lcu_credentials["auth_token"]
    port = app_state.lcu_credentials["app_port"]
    puuid = lcu_api.get_puuid(token, port, summoner_name)
    
    if not puuid:
        return jsonify({
            "success": False, 
            "message": f"找不到召唤师 '{summoner_name}' 或 LCU API 失败"
        })

    # 🚀 优化：支持自定义查询数量（默认100场，最多200场）
    count = request.args.get('count', 100, type=int)
    count = min(max(count, 1), 200)  # 限制在1-200之间
    
    # 获取战绩
    history = lcu_api.get_match_history(token, port, puuid, count=count)
    if not history:
        return jsonify({
            "success": False, 
            "message": "获取战绩失败"
        })
    
    # 处理数据
    processed_games = _process_match_history(history)
    
    # 🚀 并发查询OP.GG数据（性能优化）
    if OPGG_AVAILABLE:
        opgg_api = get_opgg_api()
        _add_opgg_data_concurrent(processed_games, opgg_api)
    
    return jsonify({
        "success": True, 
        "games": processed_games
    })


def _add_opgg_data_concurrent(games_list, opgg_api):
    """
    并发获取OP.GG数据并添加到游戏列表
    
    Args:
        games_list: 游戏列表
        opgg_api: OP.GG API实例
    """
    def fetch_single_opgg(game):
        """单个游戏的OP.GG数据获取"""
        champion_en = game.get('champion_en', '')
        if champion_en:
            try:
                return opgg_api.get_champion_stats(champion_en)
            except Exception as e:
                print(f"⚠️ 获取 {champion_en} OP.GG数据失败: {e}")
                return None
        return None
    
    # 使用线程池并发查询（最多10个并发）
    with ThreadPoolExecutor(max_workers=10) as executor:
        # 提交所有任务
        future_to_game = {
            executor.submit(fetch_single_opgg, game): game 
            for game in games_list
        }
        
        # 收集结果
        for future in as_completed(future_to_game):
            game = future_to_game[future]
            try:
                opgg_data = future.result()
                game['opgg'] = opgg_data if opgg_data else None
            except Exception as e:
                print(f"⚠️ OP.GG并发查询异常: {e}")
                game['opgg'] = None


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
            
            # 🚀 并发为每个玩家添加OP.GG数据
            if OPGG_AVAILABLE:
                opgg_api = get_opgg_api()
                
                # 收集所有玩家数据
                all_players = []
                for team in ['teamOrder', 'teamChaos']:
                    if team in formatted_data:
                        all_players.extend(formatted_data[team])
                
                # 并发查询OP.GG数据
                def fetch_player_opgg(player):
                    champion = player.get('championRaw', '').replace('game_character_displayname_', '')
                    if champion:
                        try:
                            return opgg_api.get_champion_stats(champion)
                        except:
                            return None
                    return None
                
                with ThreadPoolExecutor(max_workers=10) as executor:
                    future_to_player = {
                        executor.submit(fetch_player_opgg, player): player
                        for player in all_players
                    }
                    
                    for future in as_completed(future_to_player):
                        player = future_to_player[future]
                        try:
                            player['opgg'] = future.result()
                        except:
                            player['opgg'] = None
            
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
    
    for game in games:
        participant = game['participants'][0]
        champion_en = CHAMPION_MAP.get(participant['championId'], 'Unknown')
        stats = participant['stats']
        
        # 计算时间差
        game_creation = game.get('gameCreation', 0)
        time_diff = _calculate_time_ago(game_creation)
        
        # 提取金币和CS
        gold_earned = stats.get('goldEarned', 0)
        total_cs = stats.get('totalMinionsKilled', 0) + stats.get('neutralMinionsKilled', 0)
        
        processed_games.append({
            "champion_en": champion_en,
            "kda": f"{stats['kills']}/{stats['deaths']}/{stats['assists']}",
            "win": stats['win'],
            "gameMode": game.get('gameMode', 'UNKNOWN'),
            "mode": _format_game_mode(game.get('gameMode', '')),
            "gold": f"{gold_earned:,}",
            "cs": total_cs,
            "time_ago": time_diff,
            "duration": game.get('gameDuration', 0)
        })
    
    return processed_games


def _format_game_mode(mode):
    """格式化游戏模式名称"""
    mode_map = {
        'CLASSIC': '经典模式',
        'ARAM': '极地大乱斗',
        'URF': '无限火力',
        'ONEFORALL': '克隆模式',
        'NEXUSBLITZ': '激斗峡谷',
        'TUTORIAL': '教程',
        'PRACTICETOOL': '训练模式'
    }
    return mode_map.get(mode, mode)


def _calculate_time_ago(timestamp_ms):
    """计算时间差"""
    import time
    from datetime import datetime, timedelta
    
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
