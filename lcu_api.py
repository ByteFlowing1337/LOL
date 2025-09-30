import os
import re
import requests
from requests.auth import HTTPBasicAuth # 确保导入 HTTPBasicAuth，用于 LCU 认证
import json
import datetime
import chardet
import psutil
from time import sleep 
# 假设 LOG_DIR, constants 等在其他文件中定义，这里只保留需要的导入
from constants import LOG_DIR 
# 禁用SSL警告
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
                status_bar.showMessage(f"在日志文件中未找到所需的 --remoting-auth-token 或 --app-port 参数。")
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

    try:
        response = requests.request(
            method,
            url,
            auth=auth,
            verify=False,  # 忽略SSL证书错误
            timeout=15,
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
            print(f"!!! 权限拒绝 (403 Forbidden) !!! 可能原因: LCU 客户端限制或当前游戏状态不允许查询。")
            
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

def get_match_history(token, port, puuid):
    """
    通过 PUUID 获取比赛历史记录。
    """
    # LCU API 战绩查询端点，PUUID 在路径中
    endpoint = f"/lol-match-history/v1/products/lol/{puuid}/matches"
    
    # *** 修复 400 Bad Request 错误：移除 LCU 不再支持的 'beginIndex' 参数 ***
    return make_request(
        "GET",
        endpoint,
        token,
        port,
        params={'endIndex': 15} # 仅保留 endIndex，限制查询最近5场比赛
    )
