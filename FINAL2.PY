import requests
from requests.auth import HTTPBasicAuth
import urllib3
import json
import os
import re
from datetime import datetime
import chardet

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 日志目录路径
LOG_DIR = r"D:\WeGameApps\英雄联盟\LeagueClient"

def get_latest_log_file():
    """获取最新的日志文件"""
    try:
        # 列出所有日志文件
        log_files = [f for f in os.listdir(LOG_DIR) 
                    if f.endswith("_LeagueClientUx.log") and "T" in f]
        
        if not log_files:
            print("⚠️ 未找到日志文件，请确保游戏客户端已运行")
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
        print(f"获取日志文件时出错: {e}")
        return None

def detect_file_encoding(file_path):
    """检测文件编码"""
    try:
        # 读取文件开头部分内容检测编码
        with open(file_path, 'rb') as f:
            raw_data = f.read(4096)
            result = chardet.detect(raw_data)
            return result['encoding'] or 'gbk'
    except Exception as e:
        print(f"检测文件编码失败: {e}, 默认使用GBK")
        return 'gbk'

def extract_params_from_log(log_file):
    """从日志文件中提取认证令牌和端口号"""
    try:
        # 检测文件编码
        encoding = detect_file_encoding(log_file)
        print(f"检测到文件编码: {encoding}")
        
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
                        print(f"⚠️ 参数提取失败，第7行内容: {line[:100]}...")
        return None, None
    except Exception as e:
        print(f"读取日志文件时出错: {e}")
        return None, None

def get_puuid(auth_token, app_port, summoner_name):
    """获取召唤师的PUUID"""
    url = f"https://riot:{auth_token}@127.0.0.1:{app_port}/lol-summoner/v1/summoners"
    try:
        response = requests.get(
            url,
            params={'name': summoner_name},
            auth=HTTPBasicAuth('riot', auth_token),
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('puuid')
        else:
            print(f"获取PUUID失败! 状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
        return None

def get_match_history(auth_token, app_port, puuid):
    """获取比赛历史记录"""
    url = f"https://riot:{auth_token}@127.0.0.1:{app_port}/lol-match-history/v1/products/lol/{puuid}/matches"
    try:
        response = requests.get(
            url,
            auth=HTTPBasicAuth('riot', auth_token),
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"获取比赛记录失败! 状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
        return None

def main():
    print("="*50)
    print("英雄联盟比赛记录获取工具")
    print("="*50)
    
    # 自动获取认证令牌和端口号
    auth_token, app_port = None, None
    log_file = get_latest_log_file()
    
    if log_file:
        print(f"找到最新日志文件: {log_file}")
        auth_token, app_port = extract_params_from_log(log_file)
    
    if auth_token and app_port:
        print(f"✅ 自动获取认证令牌和端口号成功!")
        print(f"认证令牌: {auth_token}")
        print(f"应用端口: {app_port}")
    else:
        print("⚠️ 自动获取失败，请手动输入")
        auth_token = input("请输入认证令牌(auth_token): ").strip()
        app_port = input("请输入应用端口号(app_port): ").strip()
        try:
            app_port = int(app_port)
        except ValueError:
            print("❌ 端口号必须是数字")
            return
    
    summoner_name = input("\n请输入召唤师名称: ").strip()
    
    if not summoner_name:
        print("❌ 召唤师名称不能为空")
        return
    
    # 获取PUUID
    print("\n正在获取PUUID...")
    puuid = get_puuid(auth_token, app_port, summoner_name)
    
    if not puuid:
        print("❌ 无法获取PUUID，请检查输入并重试")
        return
    
    print(f"✅ 成功获取PUUID: {puuid}")
    
    # 获取比赛记录
    print("\n正在获取比赛记录...")
    match_history = get_match_history(auth_token, app_port, puuid)
    
    if match_history:
        print("\n🎮 比赛记录获取成功!")
        print("="*50)
        
        # 美化输出比赛记录
       #total_count = match_history.get('totalCount', 0)
        #print(f"总比赛场次: {total_count}")
        
        #if total_count == 0:
         #   print("没有找到比赛记录")
         #   return
        
        print("最近5场比赛:")
        
        # 提取最近的5场比赛
        games = match_history.get('games', {}).get('games', [])[:5]
        for i, game in enumerate(games, 1):
            print(f"\n比赛 #{i}:")
            print(f"模式: {game.get('gameMode', '未知模式')}")
            print(f"类型: {game.get('gameType', '未知类型')}")
            print(f"开始时间: {game.get('gameCreationDate', '未知时间')}")
            
            duration = game.get('gameDuration', 0)
            minutes, seconds = divmod(duration, 60)
            print(f"持续时间: {minutes}分{seconds}秒")
            
            # 查找玩家数据
            for participant in game.get('participants', []):
                #if participant.get('puuid') == puuid:
                    stats = participant.get('stats', {})
                    print(f"英雄ID: {participant.get('championId')}")
                    print(f"击杀/死亡/助攻: {stats.get('kills', 0)}/{stats.get('deaths', 0)}/{stats.get('assists', 0)}")
                    print(f"是否胜利: {'胜利' if stats.get('win', False) else '失败'}")
                    break
        
        print("\n完整数据已保存到 match_history.json")
        
        # 保存完整数据到文件
        try:
            with open('match_history.json', 'w', encoding='utf-8') as f:
                json.dump(match_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存文件失败: {e}")
    else:
        print("❌ 无法获取比赛记录")

if __name__ == "__main__":
    main()