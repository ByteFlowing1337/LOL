import requests
from requests.auth import HTTPBasicAuth
import urllib3
import json

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    # 用户输入
    print("="*50)
    print("英雄联盟比赛记录获取工具")
    print("="*50)
    auth_token = input("请输入认证令牌(auth_token): ").strip()
    app_port = input("请输入应用端口号(app_port): ").strip()
    summoner_name = input("请输入召唤师名称: ").strip()
    
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
        print(f"总比赛场次: {match_history.get('totalCount', 0)}")
        print("最近5场比赛:")
        
        # 提取最近的5场比赛
        games = match_history.get('games', {}).get('games', [])[:5]
        for i, game in enumerate(games, 1):
            print(f"\n比赛 #{i}:")
            print(f"模式: {game.get('gameMode', '未知模式')}")
            print(f"类型: {game.get('gameType', '未知类型')}")
            print(f"开始时间: {game.get('gameCreationDate', '未知时间')}")
            print(f"持续时间: {game.get('gameDuration', 0) // 60}分{game.get('gameDuration', 0) % 60}秒")
            # 查找玩家数据
            for participant in game.get('participants', []):
            #    if participant.get('puuid') == puuid:
                    stats = participant.get('stats', {})
                    print(f"英雄ID: {participant.get('championId')}")
                    print(f"击杀/死亡/助攻: {stats.get('kills', 0)}/{stats.get('deaths', 0)}/{stats.get('assists', 0)}")
                    print(f"是否胜利: {'胜利' if stats.get('win', False) else '失败'}")
                    break
        print("\n完整数据已保存到 match_history.json")
        
        # 保存完整数据到文件
        with open('match_history.json', 'w', encoding='utf-8') as f:
            json.dump(match_history, f, ensure_ascii=False, indent=2)
    else:
        print("❌ 无法获取比赛记录")

if __name__ == "__main__":
    main()