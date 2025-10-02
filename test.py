"""
演示如何在对局开始后获取敌方战绩的示例脚本

使用方法：
1. 启动英雄联盟客户端
2. 进入一场对局（游戏开始后）
3. 运行此脚本

功能：
- 自动检测LCU凭证
- 获取游戏内敌方玩家信息
- 查询每个敌方玩家的PUUID和战绩
"""

from lcu_api import autodetect_credentials, get_enemy_stats
import json
from time import sleep

class SimpleStatusBar:
    """简单的状态栏模拟类，用于命令行输出"""
    def showMessage(self, message):
        print(f"[状态] {message}")

def main():
    print("=" * 60)
    print("英雄联盟 - 敌方战绩查询工具")
    print("=" * 60)
    
    status_bar = SimpleStatusBar()
    
    # 步骤1: 自动检测LCU凭证
    print("\n[步骤1] 正在检测LCU凭证...")
    token, port = autodetect_credentials(status_bar)
    
    if not token or not port:
        print("\n❌ 无法获取LCU凭证，请确保：")
        print("   1. 英雄联盟客户端正在运行")
        print("   2. 已正确配置LOG_DIR路径")
        return
    
    print(f"\n✅ 凭证获取成功！")
    print(f"   Token: {token[:10]}...")
    print(f"   Port: {port}")
    
    # 步骤2: 等待游戏开始
    print("\n[步骤2] 等待游戏开始...")
    print("提示：此功能需要在对局进行中使用（加载完成后）")
    print("如果您还在选人阶段，请等待游戏开始后再试")
    
    input("\n按回车键继续查询敌方战绩...")
    
    # 步骤3: 获取敌方战绩
    print("\n[步骤3] 正在查询敌方玩家战绩...")
    print("-" * 60)
    
    enemy_stats = get_enemy_stats(token, port)
    
    if not enemy_stats:
        print("\n❌ 无法获取敌方信息，可能原因：")
        print("   1. 游戏尚未开始（还在加载界面）")
        print("   2. 不在对局中")
        print("   3. 游戏客户端API（端口2999）未响应")
        return
    
    # 步骤4: 显示结果
    print(f"\n✅ 成功获取 {len(enemy_stats)} 名敌方玩家信息！")
    print("=" * 60)
    
    for i, player in enumerate(enemy_stats, 1):
        print(f"\n【敌方玩家 {i}】")
        print(f"召唤师名: {player['summonerName']}")
        print(f"使用英雄: {player.get('championId', '未知')}")
        print(f"等级: {player.get('level', '未知')}")
        print(f"PUUID: {player.get('puuid', '无')[:30] if player.get('puuid') else '获取失败'}...")
        
        # 显示战绩摘要
        match_history = player.get('matchHistory')
        if match_history and isinstance(match_history, dict):
            games = match_history.get('games', {}).get('games', [])
            if games:
                print(f"战绩记录: {len(games)} 场比赛")
                
                # 统计胜率
                wins = sum(1 for game in games[:10] if game.get('participants', [{}])[0].get('stats', {}).get('win', False))
                total = min(len(games), 10)
                win_rate = (wins / total * 100) if total > 0 else 0
                print(f"最近{total}场胜率: {wins}胜{total-wins}负 ({win_rate:.1f}%)")
            else:
                print("战绩记录: 无数据")
        else:
            print("战绩记录: 获取失败")
        
        print("-" * 60)
    
    # 保存详细数据到文件
    output_file = "enemy_stats.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enemy_stats, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 详细数据已保存到: {output_file}")
    print("\n查询完成！")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已被用户中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
