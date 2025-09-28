
from flask import Flask, render_template, jsonify, request # 确保 request 已导入
from flask_socketio import SocketIO, emit
import threading
import time



# 导入我们已有的模块
import lcu_api
# 假设 constants 包含 CHAMPION_MAP, CHAMPION_ZH_MAP，这里无需修改
from constants import CHAMPION_MAP, CHAMPION_ZH_MAP 

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
def autodetect():
  """自动检测LCU凭证"""
  global lcu_credentials
  status_proxy = SocketIOMessageProxy()
  
  # FIX: 传入 status_proxy，解决 TypeError: autodetect_credentials() missing 1 required positional argument: 'status_bar'
  token, port = lcu_api.autodetect_credentials(status_proxy)
  
  if token and port:
    lcu_credentials["auth_token"] = token
    lcu_credentials["app_port"] = port
    return jsonify({"success": True, "token": token, "port": port})
  return jsonify({"success": False, "message": "未找到凭证，请确保游戏正在运行。"})

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
  for game in history.get('games', {}).get('games', [])[:5]: # 只取最近5场
    # FIX: 修正索引错误：participant = game['participants'][0'] -> participant = game['participants'][0]
    # 假设 'participants' 列表第一个元素就是当前召唤师的信息，这在 LCU API 返回的战绩数据中是常见的简化做法。
    participant = game['participants'][0] 
    champion_en = CHAMPION_MAP.get(participant['championId'], 'Unknown')
    champion_zh = CHAMPION_ZH_MAP.get(champion_en, champion_en)
    stats = participant['stats']
    processed_games.append({
      "champion_en": champion_en,
      "champion_zh": champion_zh,
      "kda": f"{stats['kills']}/{stats['deaths']}/{stats['assists']}",
      "win": stats['win'],
      "gameMode": game['gameMode']
    })

  return jsonify({"success": True, "games": processed_games})


# --- WebSocket 事件处理 ---

@socketio.on('connect')
def handle_connect():
  print('浏览器客户端已连接')
  emit('status_update', {'message': '已连接到本地服务器'})

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

if __name__ == '__main__':
  print("服务器启动，请在浏览器中打开 http://127.0.0.1:5000")
  socketio.run(app, host='127.0.0.1', port=5000)
