from PyQt5.QtCore import QThread, pyqtSignal
import requests
import tempfile
from requests.auth import HTTPBasicAuth
class WorkerThread(QThread):
    progress = pyqtSignal(int, str)
    result = pyqtSignal(dict, str)
    error = pyqtSignal(str)

    def __init__(self, auth_token, app_port, summoner_name):
        super().__init__()
        self.auth_token = auth_token
        self.app_port = app_port
        self.summoner_name = summoner_name

    def run(self):
        try:
            # 获取PUUID
            self.progress.emit(30, "正在获取PUUID...")
            puuid = self.get_puuid()
            
            if not puuid:
                self.error.emit("无法获取PUUID，请检查召唤师名称")
                return
            
            self.progress.emit(50, f"成功获取PUUID: {puuid}")
            
            # 获取比赛记录
            self.progress.emit(60, "正在获取比赛记录...")
            match_history = self.get_match_history(puuid)
            
            if match_history:
                self.progress.emit(100, "比赛记录获取成功!")
                self.result.emit(match_history, puuid)
            else:
                self.error.emit("无法获取比赛记录")
                
        except Exception as e:
            self.error.emit(f"发生错误: {str(e)}")

    def get_puuid(self):
        """获取召唤师的PUUID"""
        url = f"https://riot:{self.auth_token}@127.0.0.1:{self.app_port}/lol-summoner/v1/summoners"
        try:
            response = requests.get(
                url,
                params={'name': self.summoner_name},
                auth=HTTPBasicAuth('riot', self.auth_token),
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('puuid')
            else:
                self.error.emit(f"获取PUUID失败! 状态码: {response.status_code}\n响应内容: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.error.emit(f"请求异常: {e}")
            return None

    def get_match_history(self, puuid):
        """获取比赛历史记录"""
        url = f"https://riot:{self.auth_token}@127.0.0.1:{self.app_port}/lol-match-history/v1/products/lol/{puuid}/matches"
        try:
            response = requests.get(
                url,
                auth=HTTPBasicAuth('riot', self.auth_token),
                verify=False,
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.error.emit(f"获取比赛记录失败! 状态码: {response.status_code}\n响应内容: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.error.emit(f"请求异常: {e}")
            return None
class AutoAcceptThread(QThread):
    status_signal = pyqtSignal(str)  # 发送状态信息到UI
    teammate_signal = pyqtSignal(list)  # 发送队友puuid列表

    def __init__(self, auth_token, app_port):
        super().__init__()
        self.auth_token = auth_token
        self.app_port = app_port
        self.is_running = True
        self.last_phase = None
        self.processed_session = False

    def stop(self):
        self.is_running = False

    def run(self):
        while self.is_running:
            try:
                # 1. 检查游戏状态
                phase_url = f"https://riot:{self.auth_token}@127.0.0.1:{self.app_port}/lol-gameflow/v1/gameflow-phase"
                phase_response = requests.get(
                    phase_url,
                    verify=False,
                    timeout=5
                )
                
                if phase_response.status_code == 200:
                    current_phase = phase_response.json()
                    
                    # 如果阶段发生变化，重置processed_session标志
                    if current_phase != self.last_phase:
                        self.processed_session = False
                        self.last_phase = current_phase
                    
                    if current_phase == "ReadyCheck":
                        # 发现对局，自动接受
                        accept_url = f"https://riot:{self.auth_token}@127.0.0.1:{self.app_port}/lol-lobby-team-builder/v1/ready-check/accept"
                        accept_response = requests.post(
                            accept_url,
                            verify=False,
                            timeout=5
                        )
                        if accept_response.status_code == 204:
                            self.status_signal.emit("已自动接受对局")
                        else:
                            self.status_signal.emit(f"接受对局失败: {accept_response.status_code}")
                            
                    elif current_phase == "ChampSelect" and not self.processed_session:
                        # 进入英雄选择，获取队友信息
                        session_url = f"https://riot:{self.auth_token}@127.0.0.1:{self.app_port}/lol-champ-select/v1/session"
                        session_response = requests.get(
                            session_url,
                            verify=False,
                            timeout=5
                        )
                        
                        if session_response.status_code == 200:
                            session_data = session_response.json()
                            teammate_puuids = []
                            
                            # 解析我方队伍信息，获取真实puuid
                            for teammate in session_data.get('myTeam', []):
                                puuid = teammate.get('puuid')
                                if puuid and puuid != "":  # 只收集有效的puuid
                                    teammate_puuids.append({
                                        'puuid': puuid,
                                        'gameName': teammate.get('gameName', 'Unknown'),
                                        'tagLine': teammate.get('tagLine', '')
                                    })
                            
                            if teammate_puuids:
                                self.status_signal.emit(f"找到 {len(teammate_puuids)} 名队友")
                                self.teammate_signal.emit(teammate_puuids)
                                self.processed_session = True  # 标记已处理，避免重复发送
                
            except Exception as e:
                self.status_signal.emit(f"检查对局状态出错: {str(e)}")
            
            # 休眠1秒再检查
            QThread.sleep(1)
class TeammateWorkerThread(QThread):
    progress = pyqtSignal(int, str)
    result = pyqtSignal(dict, str, str, str)  # match_history, puuid, gameName, tagLine
    error = pyqtSignal(str)

    def __init__(self, auth_token, app_port, puuid, game_name, tag_line):
        super().__init__()
        self.auth_token = auth_token
        self.app_port = app_port
        self.puuid = puuid
        self.game_name = game_name
        self.tag_line = tag_line

    def run(self):
        try:
            self.progress.emit(60, f"正在获取 {self.game_name} 的比赛记录...")
            match_history = self.get_match_history()
            
            if match_history:
                self.progress.emit(100, "比赛记录获取成功!")
                self.result.emit(match_history, self.puuid, self.game_name, self.tag_line)
            else:
                self.error.emit(f"无法获取 {self.game_name} 的比赛记录")
                
        except Exception as e:
            self.error.emit(f"发生错误: {str(e)}")

    def get_match_history(self):
        """获取比赛历史记录"""
        url = f"https://riot:{self.auth_token}@127.0.0.1:{self.app_port}/lol-match-history/v1/products/lol/{self.puuid}/matches"
        try:
            response = requests.get(
                url,
                auth=HTTPBasicAuth('riot', self.auth_token),
                verify=False,
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.error.emit(f"获取比赛记录失败! 状态码: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.error.emit(f"请求异常: {e}")
            return None