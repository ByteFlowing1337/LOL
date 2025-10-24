"""
战绩查询 API
处理比赛历史记录和对局详情查询
"""
from .client import make_request


def get_match_history(token, port, puuid, count=20):
    """
    通过 PUUID 获取比赛历史记录。
    
    Args:
        token: LCU认证令牌
        port: LCU端口
        puuid: 玩家PUUID
        count: 查询数量 (默认20场，最大值通常为200)
    
    Returns:
        dict: 战绩数据，包含 games 列表
    
    Notes:
        - 查询数量越大，响应时间越长
        - 默认查询20场，响应时间约2-3秒
        - LCU API 通常支持最多 200 场历史记录
    """
    # LCU API 战绩查询端点，PUUID 在路径中
    endpoint = f"/lol-match-history/v1/products/lol/{puuid}/matches"
    
    # 动态timeout：根据查询数量调整超时时间
    # 经验值：每20场约2秒，基础3秒
    timeout = 3 + (count // 20) * 2  # 20场5秒，40场7秒，100场13秒
    timeout = min(timeout, 20)  # 最大20秒，避免等待过久
    
    print(f"📊 查询 {count} 场战绩，预计timeout={timeout}秒")
    
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
    # 🚀 性能优化：根据日志统计，将最常用的端点放在第一位
    # 经验表明 /lol-match-history/v1/games/{match_id} 是最常成功的端点
    candidates = [
        f"/lol-match-history/v1/games/{match_id}",  # ✅ 最常用，优先尝试
        f"/lol-match-history/v1/matches/{match_id}",
        f"/lol-match-history/v1/products/lol/matches/{match_id}",
        f"/lol-match-history/v1/match/{match_id}",
        f"/match/v1/matches/{match_id}",
    ]

    for ep in candidates:
        try:
            # 🔇 仅在失败时打印日志，减少控制台噪音
            res = make_request("GET", ep, token, port, timeout=3)  # 单次请求超时3秒
            if res:
                print(f"✅ 获取对局成功 (match_id={match_id})")
                return res
        except Exception as e:
            # 静默失败，继续尝试下一个端点
            continue

    # 如果都失败，打印日志供调试
    print(f"❌ 无法通过任何已知 LCU 端点获取 match_id={match_id}")
    return None
