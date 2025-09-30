
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
lcu_credentials = {
  "auth_token": None,
  "app_port": None
}
auto_accept_thread = None
thread_lock = threading.Lock()
class SocketIOMessageProxy:
  """用 Socket.IO 消息模拟 status_bar 的 showMessage 方法"""
  def showMessage(self, message):
    # 假设前端通过 'status_update' 事件接收消息
    socketio.emit('status_update', {'data': message})

# --- 后台任务 (替代 AutoAcceptThread) ---
def auto_accept_task():
  global lcu_credentials
  while True:
    if lcu_credentials["auth_token"]:
      try:
        # ⚠️ 注意：这里假设 lcu_api.get_gameflow_phase 和 lcu_api.accept_ready_check 已存在且返回正确类型
        phase = lcu_api.get_gameflow_phase(lcu_credentials["auth_token"], lcu_credentials["app_port"])
        if phase == "ReadyCheck":
          lcu_api.accept_ready_check(lcu_credentials["auth_token"], lcu_credentials["app_port"])
          socketio.emit('status_update', {'message': '已自动接受对局!'})
        
        elif phase == "ChampSelect":
          session = lcu_api.get_champ_select_session(lcu_credentials["auth_token"], lcu_credentials["app_port"])
          if session:
            teammates = []
            for team_member in session.get('myTeam', []):
              if team_member.get('puuid'):
                teammates.append({
                  'gameName': team_member.get('gameName', '未知'),
                  'tagLine': team_member.get('tagLine', ''),
                  'puuid': team_member.get('puuid')
                })
            socketio.emit('teammates_found', {'teammates': teammates})
            # 找到队友后可以暂停一段时间，避免重复发送
            time.sleep(10)

      except Exception as e:
        socketio.emit('status_update', {'message': f'后台任务出错: {e}'})
    
    time.sleep(2) # 使用 time.sleep() 在独立线程中是可以的

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
  global auto_accept_thread
  with thread_lock:
    if auto_accept_thread is None or not auto_accept_thread.is_alive():
      # 使用 time.sleep() 时，应使用普通的 threading.Thread 或确保 socketio.start_background_task 不依赖 socketio.sleep
      # 鉴于您使用了 socketio.start_background_task，推荐继续使用它并改为 time.sleep(2)
      auto_accept_thread = threading.Thread(target=auto_accept_task, daemon=True)
      auto_accept_thread.start()
      emit('status_update', {'message': '自动接受功能已开启'})

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
