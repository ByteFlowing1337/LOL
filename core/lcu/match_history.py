"""
战绩查询 API
处理比赛历史记录和对局详情查询
"""
from .client import make_request
import time

# 简单的内存缓存：{puuid: (timestamp, data)}
_match_history_cache = {}
CACHE_TTL = 300  # 缓存5分钟
MAX_CACHE_SIZE = 100  # 最大缓存100个玩家


def _clean_cache():
    """清理过期缓存和超出容量的缓存"""
    global _match_history_cache
    current_time = time.time()
    
    # 删除过期缓存
    expired_keys = [k for k, (t, _) in _match_history_cache.items() if current_time - t > CACHE_TTL]
    for k in expired_keys:
        del _match_history_cache[k]
    
    # 如果缓存过大，删除最旧的条目
    if len(_match_history_cache) > MAX_CACHE_SIZE:
        sorted_items = sorted(_match_history_cache.items(), key=lambda x: x[1][0])
        for k, _ in sorted_items[:len(_match_history_cache) - MAX_CACHE_SIZE]:
            del _match_history_cache[k]


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
        - 结果会缓存5分钟，避免重复查询
    """
    # 定期清理缓存
    _clean_cache()
    
    # 检查缓存
    cache_key = f"{puuid}_{count}"
    if cache_key in _match_history_cache:
        cached_time, cached_data = _match_history_cache[cache_key]
        if time.time() - cached_time < CACHE_TTL:
            print(f"✅ 使用缓存数据 (PUUID={puuid[:8]}..., count={count})")
            return cached_data
    
    # LCU API 战绩查询端点，PUUID 在路径中
    endpoint = f"/lol-match-history/v1/products/lol/{puuid}/matches"
    
    # 🚀 优化timeout：增加基础timeout，减少失败率
    # 经验值：每20场约2秒，基础timeout从3秒提高到8秒
    timeout = 8 + (count // 20) * 2  # 20场10秒，40场12秒，100场18秒
    timeout = min(timeout, 25)  # 最大25秒
    
    print(f"📊 查询 {count} 场战绩，预计timeout={timeout}秒")
    
    # 尝试查询，支持重试
    max_retries = 2
    for attempt in range(max_retries):
        try:
            # 查询从0到count的战绩
            result = make_request(
                "GET",
                endpoint,
                token,
                port,
                params={'endIndex': count},
                timeout=timeout  # 传入动态timeout
            )
            
            if result:
                # 缓存成功的结果
                _match_history_cache[cache_key] = (time.time(), result)
                print(f"✅ 查询成功 (PUUID={puuid[:8]}..., {len(result.get('games', []))} 场比赛)")
                return result
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️ 查询失败，{timeout}秒后重试... (attempt {attempt + 1}/{max_retries})")
                time.sleep(1)  # 等待1秒后重试
            else:
                print(f"❌ 查询最终失败 (PUUID={puuid[:8]}...): {e}")
                return None
    
    return None


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
