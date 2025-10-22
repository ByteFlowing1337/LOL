"""
内存读取API路由
提供游戏内存数据的HTTP接口
"""
from flask import Blueprint, jsonify, render_template
import logging

# 尝试导入内存读取器
try:
    from services.memory_reader import get_memory_reader
    MEMORY_READER_AVAILABLE = True
except ImportError:
    MEMORY_READER_AVAILABLE = False
    logging.warning("⚠️ 内存读取功能不可用，请安装: pip install pymem")

# 创建蓝图
memory_bp = Blueprint('memory', __name__, url_prefix='/memory')


@memory_bp.route('/')
def memory_page():
    """
    渲染内存读取页面
    
    Returns:
        HTML: 内存读取页面
    """
    return render_template('memory_reader.html')


@memory_bp.route('/status')
def get_status():
    """
    获取内存读取器状态
    
    Returns:
        JSON: 状态信息
    """
    if not MEMORY_READER_AVAILABLE:
        return jsonify({
            'success': False,
            'available': False,
            'message': '内存读取功能不可用，请安装 pymem'
        })
    
    reader = get_memory_reader()
    return jsonify({
        'success': True,
        'available': True,
        'connected': reader.is_connected,
        'message': '已连接到游戏' if reader.is_connected else '未连接'
    })


@memory_bp.route('/connect', methods=['POST'])
def connect_game():
    """
    连接到游戏进程
    
    Returns:
        JSON: 连接结果
    """
    if not MEMORY_READER_AVAILABLE:
        return jsonify({
            'success': False,
            'message': '内存读取功能不可用，请先安装: pip install pymem'
        })
    
    # 检查是否有管理员权限
    import ctypes
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False
    
    if not is_admin:
        return jsonify({
            'success': False,
            'message': '❌ 需要管理员权限！\n\n请执行以下步骤:\n1. 关闭当前程序\n2. 右键程序图标 → 以管理员身份运行\n3. 重新尝试连接',
            'error_code': 'NO_ADMIN'
        })
    
    reader = get_memory_reader()
    
    if reader.is_connected:
        return jsonify({
            'success': True,
            'message': '已经连接到游戏'
        })
    
    success = reader.connect()
    
    if success:
        # 连接成功后启动自动更新
        reader.start_auto_update(interval=0.5)
        
        return jsonify({
            'success': True,
            'message': '✅ 成功连接到游戏进程！'
        })
    else:
        return jsonify({
            'success': False,
            'message': '❌ 连接失败\n\n可能的原因:\n1. 游戏未在对局中（需要进入对局）\n2. 游戏使用了反调试保护\n3. 进程架构不匹配（请使用64位Python）\n4. 游戏未完全加载\n\n解决方法:\n1. 进入训练模式或人机对局\n2. 等待游戏完全加载\n3. 重新点击"连接游戏"\n\n详细日志请查看终端窗口',
            'error_code': 'CONNECTION_FAILED'
        })


@memory_bp.route('/disconnect', methods=['POST'])
def disconnect_game():
    """
    断开游戏连接
    
    Returns:
        JSON: 断开结果
    """
    if not MEMORY_READER_AVAILABLE:
        return jsonify({
            'success': False,
            'message': '内存读取功能不可用'
        })
    
    reader = get_memory_reader()
    reader.stop_auto_update()
    reader.disconnect()
    
    return jsonify({
        'success': True,
        'message': '已断开连接'
    })


@memory_bp.route('/player_data')
def get_player_data():
    """
    获取玩家数据
    
    Returns:
        JSON: 玩家数据
    """
    if not MEMORY_READER_AVAILABLE:
        return jsonify({
            'success': False,
            'message': '内存读取功能不可用'
        })
    
    reader = get_memory_reader()
    
    if not reader.is_connected:
        return jsonify({
            'success': False,
            'message': '未连接到游戏，请先连接'
        })
    
    data = reader.get_cached_data()
    
    return jsonify({
        'success': True,
        'data': data
    })


@memory_bp.route('/spell_cooldowns')
def get_spell_cooldowns():
    """
    获取技能冷却时间
    
    Returns:
        JSON: 技能CD数据
    """
    if not MEMORY_READER_AVAILABLE:
        return jsonify({
            'success': False,
            'message': '内存读取功能不可用'
        })
    
    reader = get_memory_reader()
    
    if not reader.is_connected:
        return jsonify({
            'success': False,
            'message': '未连接到游戏'
        })
    
    cooldowns = reader.get_spell_cooldowns()
    
    return jsonify({
        'success': True,
        'data': cooldowns
    })


@memory_bp.route('/game_time')
def get_game_time():
    """
    获取游戏时间
    
    Returns:
        JSON: 游戏时间
    """
    if not MEMORY_READER_AVAILABLE:
        return jsonify({
            'success': False,
            'message': '内存读取功能不可用'
        })
    
    reader = get_memory_reader()
    
    if not reader.is_connected:
        return jsonify({
            'success': False,
            'message': '未连接到游戏'
        })
    
    game_time = reader.get_game_time()
    minutes = int(game_time // 60)
    seconds = int(game_time % 60)
    
    return jsonify({
        'success': True,
        'data': {
            'total_seconds': game_time,
            'minutes': minutes,
            'seconds': seconds,
            'formatted': f"{minutes:02d}:{seconds:02d}"
        }
    })
