
from flask import Flask, render_template, jsonify, request # 确保 request 已导入
from flask_socketio import SocketIO, emit
import threading
import time,socket
import webbrowser # 用于在浏览器中打开地址



# 导入我们已有的模块
import lcu_api
# 假设 constants 包含 CHAMPION_MAP, CHAMPION_ZH_MAP，这里无需修改
from constants import CHAMPION_MAP

# --- Flask 和 SocketIO 初始化 ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secret_key' # 用于session加密
socketio = SocketIO(app, async_mode='threading') # 使用 threading 模式

# --- 全局变量来存储LCU凭证和后台线程 ---
auto_accept_enabled = False  # 自动接受对局开关
auto_analyze_enabled = False  # 敌我分析开关
teammate_analysis_done = False  # 队友分析完成标志
enemy_analysis_done = False  # 敌人分析完成标志
current_teammates = set()  # 当前队友的 PUUID 集合

lcu_credentials = {
  "auth_token": None,
  "app_port": None
}
auto_accept_thread = None
auto_analyze_thread = None
thread_lock = threading.Lock()
class SocketIOMessageProxy:
    """用 Socket.IO 消息模拟 status_bar 的 showMessage 方法"""
    def showMessage(self, message):
        # 假设前端通过 'status_update' 事件接收消息
        socketio.emit('status_update', {'data': message})
        # 同时在控制台输出，方便调试
        print(f"[LCU连接] {message}")

# --- 后台任务1: 自动接受对局 ---
def auto_accept_task():
    global lcu_credentials, auto_accept_enabled
    
    while True:
        if auto_accept_enabled and lcu_credentials["auth_token"]:
            try:
                token = lcu_credentials["auth_token"]
                port = lcu_credentials["app_port"]
                
                phase = lcu_api.get_gameflow_phase(token, port)
                
                # ReadyCheck 阶段：自动接受对局
                if phase == "ReadyCheck":
                    try:
                        lcu_api.accept_ready_check(token, port)
                        socketio.emit('status_update', {'message': '✅ 已自动接受对局!'})
                        print("✅ 自动接受对局成功")
                    except Exception as accept_error:
                        print(f"⚠️ 自动接受对局失败: {accept_error}")
                        socketio.emit('status_update', {'message': f'⚠️ 自动接受失败: {accept_error}'})
                
            except Exception as e:
                print(f"❌ 自动接受任务异常: {e}")
            
            time.sleep(1)  # 快速轮询
        else:
            time.sleep(2)

# --- 后台任务2: 敌我分析 ---
def auto_analyze_task():
    global lcu_credentials, enemy_analysis_done, teammate_analysis_done, auto_analyze_enabled, current_teammates
    enemy_retry_count = 0  # 敌人分析重试计数器
    MAX_ENEMY_RETRIES = 10  # 最大重试次数
    last_phase = None  # 记录上一次的游戏阶段
    
    while True:
        if auto_analyze_enabled and lcu_credentials["auth_token"]:
            try:
                token = lcu_credentials["auth_token"]
                port = lcu_credentials["app_port"]
                
                phase = lcu_api.get_gameflow_phase(token, port)
                
                # 检测到新的游戏流程开始（从 Lobby/None 进入其他阶段），重置状态
                if last_phase in ["Lobby", "None", None] and phase not in ["Lobby", "None"]:
                    teammate_analysis_done = False
                    enemy_analysis_done = False
                    enemy_retry_count = 0
                    current_teammates.clear()  # 清空队友PUUID集合
                    print(f"🔄 检测到新游戏流程开始 ({last_phase} -> {phase})，重置分析状态")
                
                # ChampSelect 阶段：分析队友战绩（仅一次）
                elif phase == "ChampSelect" and not teammate_analysis_done:
                    session = lcu_api.get_champ_select_session(token, port)
                    if session:
                        teammates = []
                        for team_member in session.get('myTeam', []):
                            puuid = team_member.get('puuid')
                            if puuid:
                                current_teammates.add(puuid)  # 记录队友PUUID
                                teammates.append({
                                    'gameName': team_member.get('gameName', '未知'),
                                    'tagLine': team_member.get('tagLine', ''),
                                    'puuid': puuid
                                })
                        
                        if teammates:
                            socketio.emit('teammates_found', {'teammates': teammates})
                            socketio.emit('status_update', {'message': f'👥 发现 {len(teammates)} 名队友，开始分析战绩...'})
                            teammate_analysis_done = True  # 标记队友已分析，避免重复
                            print(f"✅ 队友分析完成，共 {len(teammates)} 人")
                            print(f"📝 记录队友PUUID集合: {len(current_teammates)} 人")
                
                # InProgress/GameStart 阶段：只分析敌人（从10人中过滤队友）
                elif phase in ["InProgress", "GameStart"] and not enemy_analysis_done:
                    if enemy_retry_count < MAX_ENEMY_RETRIES:
                        enemy_retry_count += 1
                        socketio.emit('status_update', {'message': f'🔍 正在获取敌方信息... (尝试 {enemy_retry_count}/{MAX_ENEMY_RETRIES})'})
                        print(f"开始第 {enemy_retry_count} 次尝试获取敌方信息")
                        
                        # 调用新的API获取所有玩家（前5队友，后5敌人）
                        players_data = lcu_api.get_all_players_from_game(token, port)
                        
                        if players_data:
                            enemies = players_data.get('enemies', [])
                            
                            # 如果已记录队友PUUID，则进行双重过滤（更安全）
                            if current_teammates:
                                filtered_enemies = []
                                for enemy in enemies:
                                    if enemy.get('puuid') and enemy['puuid'] not in current_teammates:
                                        filtered_enemies.append(enemy)
                                    elif enemy.get('puuid') in current_teammates:
                                        print(f"🚫 过滤队友: {enemy.get('summonerName', '未知')}")
                                enemies = filtered_enemies
                            
                            if len(enemies) > 0:
                                socketio.emit('enemies_found', {'enemies': enemies})
                                socketio.emit('status_update', {'message': f'💥 发现 {len(enemies)} 名敌人，开始分析战绩...'})
                                enemy_analysis_done = True  # 标记敌人已分析完成
                                print(f"✅ 敌人分析完成，共 {len(enemies)} 人")
                            else:
                                print(f"⚠️ 第 {enemy_retry_count} 次尝试：过滤后无敌人数据")
                                time.sleep(3)  # 等待3秒后重试
                        else:
                            print(f"⚠️ 第 {enemy_retry_count} 次尝试：未获取到游戏数据")
                            time.sleep(3)  # 等待3秒后重试
                    else:
                        # 达到最大重试次数
                        socketio.emit('status_update', {'message': '❌ 无法获取敌方信息，已停止重试'})
                        enemy_analysis_done = True
                        print(f"❌ 达到最大重试次数 ({MAX_ENEMY_RETRIES})，停止尝试")
                
                # EndOfGame 阶段：显示提示
                elif phase == "EndOfGame":
                    if teammate_analysis_done or enemy_analysis_done:  # 只在有分析过的情况下显示
                        socketio.emit('status_update', {'message': '🏁 比赛结束，等待下一局...'})
                        print("🏁 游戏结束")
                
                # 更新上一次的阶段
                last_phase = phase

            except Exception as e:
                # 捕获异常时的处理
                error_msg = f'敌我分析任务出错: {str(e)}'
                socketio.emit('status_update', {'message': f'❌ {error_msg}'})
                print(f"❌ 异常: {error_msg}")
                # 发生异常时，稍微等待后继续
                time.sleep(5)
            
            # 每次循环结束后的等待时间
            if phase in ["InProgress", "GameStart"] and not enemy_analysis_done:
                time.sleep(1)  # 游戏中重试，等待1秒
            else:
                time.sleep(2)  # 其他情况等待2秒
        else:
            # 如果功能未开启或凭证不存在，等待
            time.sleep(2)


# --- HTTP 路由 (Endpoints) ---

@app.route('/')
def index():
  """渲染主页面"""
  return render_template('index.html')

@app.route('/autodetect', methods=['POST'])
# app.py 中的 detect_and_connect_lcu 函数

def detect_and_connect_lcu(status_proxy):
    """后台任务：尝试获取 LCU 凭证"""
    global lcu_credentials
    
    status_proxy.showMessage("正在自动检测英雄联盟客户端 (进程和凭证)...")
    
    # 🎯 使用 lcu_api.autodetect_credentials，它现在包含了进程检测
    token, port = lcu_api.autodetect_credentials(status_proxy)

    if token and port:
        lcu_credentials["auth_token"] = token
        lcu_credentials["app_port"] = port
        # 通知前端最终的成功状态
        status_proxy.showMessage(f"✅ LCU 连接成功！端口: {port}。")
    else:
        lcu_credentials["auth_token"] = None
        lcu_credentials["app_port"] = None
        # 注意：失败的详细原因会由 lcu_api.autodetect_credentials 里的 showMessage 发送。
        # 这里的提示作为最终的失败结论。
        status_proxy.showMessage("❌ 连接 LCU 失败。请检查客户端是否运行或重启程序。")

# 核心修改点在这里
@app.route('/get_history', methods=['GET'])
def get_history():
  """获取指定召唤师的战绩 (使用查询参数 name)"""
  # 1. 从查询参数中获取召唤师名称
  summoner_name = request.args.get('name')
  
  if not summoner_name:
    return jsonify({"success": False, "message": "请求缺少召唤师名称 (name) 查询参数"})

  if not lcu_credentials["auth_token"]:
    return jsonify({"success": False, "message": "未连接到客户端"})

  # 2. 调用 lcu_api 获取 puuid
  puuid = lcu_api.get_puuid(lcu_credentials["auth_token"], lcu_credentials["app_port"], summoner_name)
  
  if not puuid:
    return jsonify({"success": False, "message": f"找不到召唤师 '{summoner_name}' 或 LCU API 失败"})

  # ⚠️ 注意：lcu_api.get_match_history 需要在 lcu_api.py 中实现
  history = lcu_api.get_match_history(lcu_credentials["auth_token"], lcu_credentials["app_port"], puuid)
  if not history:
    return jsonify({"success": False, "message": "获取战绩失败"})
    
  # 对数据进行一些处理，方便前端展示
  processed_games = []
  for game in history.get('games', {}).get('games', [])[:10]: # 只取最近5场
    # FIX: 修正索引错误：participant = game['participants'][0'] -> participant = game['participants'][0]
    # 假设 'participants' 列表第一个元素就是当前召唤师的信息，这在 LCU API 返回的战绩数据中是常见的简化做法。
    participant = game['participants'][0] 
    champion_en = CHAMPION_MAP.get(participant['championId'], 'Unknown')
   # champion_zh = CHAMPION_ZH_MAP.get(champion_en, champion_en)
    stats = participant['stats']
    processed_games.append({
      "champion_en": champion_en,
      # "champion_zh": champion_zh,
      "kda": f"{stats['kills']}/{stats['deaths']}/{stats['assists']}",
      "win": stats['win'],
      "gameMode": game['gameMode']
    })

  return jsonify({"success": True, "games": processed_games})


# --- WebSocket 事件处理 ---

@socketio.on('connect')
def handle_connect():
  print('浏览器客户端已连接，触发自动检测...')
  # 创建状态代理，用于将消息发送回浏览器
  status_proxy = SocketIOMessageProxy()
  status_proxy.showMessage('已连接到本地服务器，开始自动检测LCU...')
  

  socketio.start_background_task(detect_and_connect_lcu, status_proxy)

@socketio.on('start_auto_accept')
def handle_start_auto_accept():
  global auto_accept_thread, auto_accept_enabled
  with thread_lock:
    if auto_accept_thread is None or not auto_accept_thread.is_alive():
      auto_accept_enabled = True
      auto_accept_thread = threading.Thread(target=auto_accept_task, daemon=True)
      auto_accept_thread.start()
      emit('status_update', {'message': '✅ 自动接受对局功能已开启'})
      print("🎮 自动接受对局功能已启动")
    else:
      emit('status_update', {'message': '⚠️ 自动接受功能已在运行中'})

@socketio.on('start_auto_analyze')
def handle_start_auto_analyze():
  global auto_analyze_thread, auto_analyze_enabled
  with thread_lock:
    if auto_analyze_thread is None or not auto_analyze_thread.is_alive():
      auto_analyze_enabled = True
      auto_analyze_thread = threading.Thread(target=auto_analyze_task, daemon=True)
      auto_analyze_thread.start()
      emit('status_update', {'message': '✅ 敌我分析功能已开启'})
      print("📊 敌我分析功能已启动")
    else:
      emit('status_update', {'message': '⚠️ 敌我分析功能已在运行中'})

# 注意：为了简化，这里没有提供停止后台任务的逻辑，在实际应用中需要添加。
def get_local_ip():
    """尝试获取本地局域网（内网）IP地址。"""
    try:
        # 创建一个UDP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 尝试连接一个外部地址（例如 Google DNS），但数据不会真正发送
        # 这一步是为了让操作系统选择一个合适的网络接口，从而获取到对应的内网IP
        s.connect(('10.255.255.255', 1))
        # 获取socket连接的本机地址
        ip_address = s.getsockname()[0]
    except Exception:
        # 如果获取失败，则使用本地回环地址
        ip_address = '127.0.0.1'
    finally:
        s.close()
    return ip_address
if __name__ == '__main__':
    local_ip = get_local_ip()
    server_address = f'http://{local_ip}:5000'
    def open_browser():
        print(f"尝试在浏览器中打开: {server_address}")
        webbrowser.open(server_address)
        
    # 延迟 0.5 秒启动浏览器
    threading.Timer(0.5, open_browser).start()
    
    # 输出启动信息，同时提示用户可以使用局域网 IP 访问
    print(f"LOLHelperWeb已启动！")
    print(f"本机访问地址: http://127.0.0.1:5000")
    print(f"局域网访问地址: {server_address} (请确保防火墙已允许)")
    
    socketio.run(app, host='0.0.0.0', port=5000)
