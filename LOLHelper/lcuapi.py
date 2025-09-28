# lcu_api.py

import requests
from requests.auth import HTTPBasicAuth
import os
import re
from datetime import datetime
import chardet
import urllib3

from cons import LOG_DIR

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_latest_log_file(self):
        """获取最新的日志文件"""
        try:
            # 列出所有日志文件
            log_files = [f for f in os.listdir(LOG_DIR) 
                        if f.endswith("_LeagueClientUx.log") and "T" in f]
            
            if not log_files:
                return None
            
            # 提取文件名中的时间戳并排序
            def extract_time(f):
                try:
                    # 文件名格式: 2025-07-12T12-23-05_18520_LeagueClientUx.log
                    time_str = f.split("T")[0] + "T" + f.split("T")[1].split("_")[0]
                    return datetime.strptime(time_str, "%Y-%m-%dT%H-%M-%S")
                except:
                    return datetime.min
            
            # 获取最新文件
            latest_file = max(log_files, key=extract_time)
            return os.path.join(LOG_DIR, latest_file)
        
        except Exception as e:
            self.status_bar.showMessage(f"获取日志文件时出错: {e}")
            return None
def detect_file_encoding(self, file_path):
        """检测文件编码"""
        try:
            # 读取文件开头部分内容检测编码
            with open(file_path, 'rb') as f:
                raw_data = f.read(4096)
                result = chardet.detect(raw_data)
                return result['encoding'] or 'gbk'
        except Exception as e:
            self.status_bar.showMessage(f"检测文件编码失败: {e}, 默认使用GBK")
            return 'gbk'
def extract_params_from_log(self, log_file):
        """从日志文件中提取认证令牌和端口号"""
        try:
            # 检测文件编码
            encoding = self.detect_file_encoding(log_file)
            self.status_bar.showMessage(f"检测到文件编码: {encoding}")
            
            with open(log_file, "r", encoding=encoding, errors='replace') as f:
                # 读取前7行（第7行包含参数）
                for i in range(7):
                    line = f.readline().strip()
                    if i == 6:  # 第7行
                        # 使用正则表达式提取参数
                        token_match = re.search(r"--remoting-auth-token=([\w-]+)", line)
                        port_match = re.search(r"--app-port=(\d+)", line)
                        
                        if token_match and port_match:
                            return token_match.group(1), int(port_match.group(1))
                        else:
                            self.status_bar.showMessage(f"参数提取失败，第7行内容: {line[:100]}...")
            return None, None
        except Exception as e:
            self.status_bar.showMessage(f"读取日志文件时出错: {e}")
            return None, None

def autodetect_credentials():
    """组合函数，自动检测并返回认证信息"""
    log_file = get_latest_log_file()
    if log_file:
        return extract_params_from_log(log_file)
    return None, None

def make_request(method, endpoint, auth_token, app_port, **kwargs):
    """通用的请求函数"""
    url = f"https://riot:{auth_token}@127.0.0.1:{app_port}{endpoint}"
    try:
        response = requests.request(
            method,
            url,
            auth=HTTPBasicAuth('riot', auth_token),
            verify=False,
            timeout=15,
            **kwargs
        )
        return response
    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
        return None

# --- 下面是具体的API功能封装 ---

def get_puuid(auth_token, app_port, summoner_name):
    """获取召唤师的PUUID"""
    response = make_request('get', '/lol-summoner/v1/summoners', auth_token, app_port, params={'name': summoner_name})
    if response and response.status_code == 200:
        return response.json().get('puuid')
    return None

def get_match_history(auth_token, app_port, puuid):
    """获取比赛历史记录"""
    endpoint = f"/lol-match-history/v1/products/lol/{puuid}/matches"
    response = make_request('get', endpoint, auth_token, app_port)
    if response and response.status_code == 200:
        return response.json()
    return None

def get_gameflow_phase(auth_token, app_port):
    """检查游戏状态"""
    response = make_request('get', '/lol-gameflow/v1/gameflow-phase', auth_token, app_port)
    if response and response.status_code == 200:
        return response.json()
    return None

def accept_ready_check(auth_token, app_port):
    """接受对局"""
    endpoint = "/lol-lobby-team-builder/v1/ready-check/accept"
    response = make_request('post', endpoint, auth_token, app_port)
    return response and response.status_code == 204

def get_champ_select_session(auth_token, app_port):
    """获取英雄选择会话信息"""
    response = make_request('get', '/lol-champ-select/v1/session', auth_token, app_port)
    if response and response.status_code == 200:
        return response.json()
    return None

def select_champion_action(auth_token, app_port, action_id, champion_id):
    """执行选择英雄的动作"""
    endpoint = f"/lol-champ-select/v1/session/actions/{action_id}"
    payload = {"championId": champion_id, "completed": True}
    response = make_request('patch', endpoint, auth_token, app_port, json=payload)
    return response and response.status_code == 204