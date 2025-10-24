"""
召唤师信息 API
查询召唤师资料、PUUID 等信息
"""
import re
from .client import make_request


def get_current_summoner(token, port):
    """
    获取当前登录召唤师的完整信息。
    
    返回数据包含:
    - summonerId: 召唤师ID
    - displayName: 显示名称
    - puuid: PUUID
    - profileIconId: 头像ID
    - summonerLevel: 等级
    
    Args:
        token: LCU认证令牌
        port: LCU端口
    
    Returns:
        dict: 召唤师信息
    """
    return make_request("GET", "/lol-summoner/v1/current-summoner", token, port)


def get_puuid(token, port, summoner_name):
    """
    通过召唤师名字获取PUUID。
    
    使用 LCU API /lol-summoner/v1/summoners?name={summoner_name} 查询。
    会自动清理名称中的 Unicode 控制字符（如 Bidi 字符）。
    
    Args:
        token: LCU认证令牌
        port: LCU端口
        summoner_name: 召唤师名称（支持 GameName#TAG 格式）
    
    Returns:
        str: PUUID，失败返回None
    """
    endpoint = "/lol-summoner/v1/summoners"
    
    # 移除不可见的 Unicode 控制字符 (如 U+206E, U+2069 等 Bidi 字符)
    # 同时保留 # 号用于 Riot ID 格式
    CLEANR = re.compile(r'[\u200e-\u200f\u202a-\u202e\u2066-\u2069]')
    cleaned_name = re.sub(CLEANR, '', summoner_name).strip() 

    # 使用 make_request 发送请求
    data = make_request(
        "GET",
        endpoint,
        token,
        port,
        params={'name': cleaned_name}  # 使用查询参数传递清洗后的名称
    )
    
    if data:
        # Riot ID 查询返回的是一个包含 puuid 的字典
        return data.get('puuid')
    return None


def get_summoner_by_id(token, port, summoner_id):
    """
    通过 summonerId 获取召唤师信息。
    
    Args:
        token: LCU认证令牌
        port: LCU端口
        summoner_id: 召唤师ID
    
    Returns:
        dict: 召唤师信息
    """
    endpoint = f"/lol-summoner/v1/summoners/{summoner_id}"
    return make_request("GET", endpoint, token, port)


def get_summoner_by_puuid(token, port, puuid):
    """
    通过 puuid 获取召唤师信息。
    
    Args:
        token: LCU认证令牌
        port: LCU端口
        puuid: 玩家PUUID
    
    Returns:
        dict: 召唤师信息
    """
    endpoint = f"/lol-summoner/v1/summoners/by-puuid/{puuid}"
    return make_request("GET", endpoint, token, port)


def get_summoner_by_name(token, port, name):
    """
    通过召唤师名字查询完整信息。
    
    使用 ?name= 查询参数，LCU 返回字典格式。
    
    Args:
        token: LCU认证令牌
        port: LCU端口
        name: 召唤师名称
    
    Returns:
        dict: 召唤师信息
    """
    endpoint = "/lol-summoner/v1/summoners"
    return make_request("GET", endpoint, token, port, params={'name': name})
