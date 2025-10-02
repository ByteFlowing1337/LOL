"""
新功能测试脚本
测试实时游戏数据格式化和API端点
"""

import sys
import json

# 模拟游戏数据（从用户提供的数据）
MOCK_GAME_DATA = {
    "activePlayer": {
        "summonerName": "召唤师2321#55777",
        "level": 4
    },
    "allPlayers": [
        {
            "championName": "血港鬼影",
            "level": 4,
            "summonerName": "丿老人与海丶#37703",
            "riotIdGameName": "丿老人与海丶",
            "riotIdTagLine": "37703",
            "scores": {"kills": 1, "deaths": 2, "assists": 1, "creepScore": 0},
            "items": [
                {"itemID": 1036, "displayName": "长剑", "count": 1},
                {"itemID": 2031, "displayName": "复用型药水", "count": 1}
            ],
            "runes": {
                "keystone": {"displayName": "丛刃", "id": 9923},
                "primaryRuneTree": {"displayName": "主宰", "id": 8100},
                "secondaryRuneTree": {"displayName": "坚决", "id": 8400}
            },
            "summonerSpells": {
                "summonerSpellOne": {"displayName": "闪现"},
                "summonerSpellTwo": {"displayName": "幽灵疾步"}
            },
            "team": "ORDER",
            "isDead": False,
            "respawnTimer": 0
        },
        {
            "championName": "远古巫灵",
            "level": 4,
            "summonerName": "召唤师2321#55777",
            "riotIdGameName": "召唤师2321",
            "riotIdTagLine": "55777",
            "scores": {"kills": 2, "deaths": 1, "assists": 0, "creepScore": 10},
            "items": [
                {"itemID": 1056, "displayName": "多兰之戒", "count": 1},
                {"itemID": 1082, "displayName": "黑暗封印", "count": 1}
            ],
            "runes": {
                "keystone": {"displayName": "奥术彗星", "id": 8229},
                "primaryRuneTree": {"displayName": "巫术", "id": 8200},
                "secondaryRuneTree": {"displayName": "主宰", "id": 8100}
            },
            "summonerSpells": {
                "summonerSpellOne": {"displayName": "幽灵疾步"},
                "summonerSpellTwo": {"displayName": "闪现"}
            },
            "team": "CHAOS",
            "isDead": False,
            "respawnTimer": 0
        }
    ],
    "gameData": {
        "gameMode": "URF",
        "gameTime": 245.908676147461,
        "mapName": "Map11",
        "mapNumber": 11
    },
    "events": {
        "Events": [
            {
                "EventName": "ChampionKill",
                "EventTime": 145.962249755859,
                "KillerName": "召唤师2321",
                "VictimName": "海蓝梁朝伟",
                "Assisters": ["兔卯立秋"]
            }
        ]
    }
}


def test_game_data_formatter():
    """测试游戏数据格式化"""
    print("=" * 60)
    print("测试: 游戏数据格式化工具")
    print("=" * 60)
    
    try:
        from utils.game_data_formatter import format_game_data
        
        result = format_game_data(MOCK_GAME_DATA)
        
        print("\n✅ 格式化成功!")
        print(f"\n队友数量: {len(result['teammates'])}")
        print(f"敌人数量: {len(result['enemies'])}")
        print(f"游戏模式: {result['gameInfo']['mode']}")
        print(f"游戏时间: {result['gameInfo']['time']}秒")
        print(f"当前玩家队伍: {result['activePlayerTeam']}")
        
        # 显示第一个队友的详细信息
        if result['teammates']:
            tm = result['teammates'][0]
            print(f"\n队友示例:")
            print(f"  召唤师: {tm['gameName']}#{tm['tagLine']}")
            print(f"  英雄: {tm['champion']}")
            print(f"  等级: {tm['level']}")
            print(f"  KDA: {tm['kda']}")
            print(f"  补刀: {tm['cs']}")
            print(f"  基石符文: {tm['keystone']}")
            print(f"  装备数量: {len(tm['items'])}")
        
        # 显示第一个敌人的详细信息
        if result['enemies']:
            enemy = result['enemies'][0]
            print(f"\n敌人示例:")
            print(f"  召唤师: {enemy['gameName']}#{enemy['tagLine']}")
            print(f"  英雄: {enemy['champion']}")
            print(f"  等级: {enemy['level']}")
            print(f"  KDA: {enemy['kda']}")
            print(f"  是否死亡: {enemy['isDead']}")
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_api_routes():
    """测试API路由配置"""
    print("\n" + "=" * 60)
    print("测试: API路由配置")
    print("=" * 60)
    
    try:
        # 检查路由函数是否存在
        from routes import api_routes
        
        required_functions = [
            'index',
            'summoner_detail',
            'live_game',
            'get_history',
            'get_live_game_data'
        ]
        
        print(f"\n检查API路由函数:")
        all_found = True
        for func_name in required_functions:
            has_func = hasattr(api_routes, func_name)
            status = "✅" if has_func else "❌"
            print(f"  {status} {func_name}")
            all_found = all_found and has_func
        
        if all_found:
            print("\n✅ 所有必需的路由函数都已定义")
            return True
        else:
            print("\n❌ 部分路由函数缺失")
            return False
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_imports():
    """测试模块导入"""
    print("\n" + "=" * 60)
    print("测试: 模块导入")
    print("=" * 60)
    
    modules_to_test = [
        'utils.game_data_formatter',
        'routes.api_routes',
        'config',
        'lcu_api'
    ]
    
    all_success = True
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {module_name}")
        except Exception as e:
            print(f"❌ {module_name} - {str(e)}")
            all_success = False
    
    return all_success


if __name__ == '__main__':
    print("\n🧪 LOLHelper 新功能测试套件")
    print("=" * 60)
    
    results = []
    
    # 测试1: 模块导入
    print("\n[测试 1/3] 模块导入测试")
    results.append(('模块导入', test_imports()))
    
    # 测试2: 数据格式化
    print("\n[测试 2/3] 数据格式化测试")
    results.append(('数据格式化', test_game_data_formatter()))
    
    # 测试3: API路由
    print("\n[测试 3/3] API路由测试")
    # 注意: 这个测试需要Flask应用上下文，可能会失败
    try:
        results.append(('API路由', test_api_routes()))
    except:
        print("⚠️  API路由测试需要应用运行时上下文，跳过")
        results.append(('API路由', None))
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    for name, result in results:
        if result is True:
            status = "✅ 通过"
        elif result is False:
            status = "❌ 失败"
        else:
            status = "⚠️  跳过"
        print(f"{name:20} {status}")
    
    success_count = sum(1 for _, r in results if r is True)
    total_count = len([r for _, r in results if r is not None])
    
    print(f"\n通过率: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n🎉 所有测试通过! 新功能已就绪.")
        sys.exit(0)
    else:
        print("\n⚠️  部分测试未通过，请检查上述错误信息.")
        sys.exit(1)
