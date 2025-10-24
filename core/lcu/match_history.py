"""
战绩查询 API
处理比赛历史记录和对局详情查询
"""
from .client import make_request


def get_match_history(token, port, puuid, count=100):
    """
    通过 PUUID 获取比赛历史记录。
    
    Args:
        token: LCU认证令牌
        port: LCU端口
        puuid: 玩家PUUID
        count: 查询数量 (默认100场，最大值通常为200)
    
    Returns:
        dict: 战绩数据，包含 games 列表
    
    Notes:
        - 查询数量越大，响应时间越长
        - 建议分批查询以提高响应速度
        - LCU API 通常支持最多 200 场历史记录
    """
    # LCU API 战绩查询端点，PUUID 在路径中
    endpoint = f"/lol-match-history/v1/products/lol/{puuid}/matches"
    
    # 动态timeout：根据查询数量调整超时时间
    # 经验值：每100场约需5秒，基础5秒 + 额外时间
    timeout = 5 + (count // 50) * 3  # 50场+3秒，100场+6秒，200场+12秒
    timeout = min(timeout, 20)  # 最大20秒，避免等待过久
    
    print(f"📊 查询 {count} 场战绩，timeout={timeout}秒")
    
    # 查询从0到count的战绩
    return make_request(
        "GET",
        endpoint,
        token,
        port,
        params={'endIndex': count},
        timeout=timeout  # 传入动态timeout
    )


def get_match_by_id(token, port, match_id):
    """
    通过 match_id 获取完整对局详情。
    
    尝试多个可能的 LCU 端点，返回第一个成功的响应。
    不同版本的 LCU 或打包服务器可能使用不同的路径。
    
    Args:
        token: LCU认证令牌
        port: LCU端口
        match_id: 对局ID
    
    Returns:
        dict: 对局完整数据，失败返回None
    """
    # 尝试多个已知/可能的内部端点
    candidates = [
        f"/lol-match-history/v1/matches/{match_id}",
        f"/lol-match-history/v1/products/lol/matches/{match_id}",
        f"/lol-match-history/v1/games/{match_id}",
        f"/lol-match-history/v1/match/{match_id}",
        f"/match/v1/matches/{match_id}",
    ]

    for ep in candidates:
        try:
            print(f"尝试通过 LCU 端点获取对局: {ep}")
            res = make_request("GET", ep, token, port)
            if res:
                print(f"✅ 通过端点 {ep} 成功获取对局")
                return res
        except Exception as e:
            print(f"尝试端点 {ep} 时出现异常: {e}")

    # 如果都失败，打印日志供调试
    print(f"❌ 无法通过任何已知 LCU 端点获取 match_id={match_id}")
    return None
