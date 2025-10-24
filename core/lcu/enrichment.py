"""
数据增强模块
为游戏数据填充缺失的召唤师信息
"""
from .summoner import get_summoner_by_puuid, get_summoner_by_id, get_summoner_by_name


def enrich_game_with_summoner_info(token, port, game):
    """
    为 game['participants'] 中的每个参与者填充缺失的召唤师信息。
    
    尝试通过以下方式获取信息:
    1. 通过 puuid 查询
    2. 通过 summonerId 查询
    3. 通过 summonerName 查询
    4. 从 participantIdentities 中提取（备用）
    
    Args:
        token: LCU认证令牌
        port: LCU端口
        game: 游戏数据对象（dict）
    
    Returns:
        dict: 增强后的游戏数据（就地修改并返回）
    
    Notes:
        - 此函数会就地修改传入的 game 对象
        - 填充字段: summonerName, profileIcon, puuid
        - 如果所有方法都失败，会尝试从 participantIdentities 中提取
    """
    if not game or not isinstance(game, dict):
        return game

    participants = game.get('participants') or []
    
    # 构建 participantIdentities 映射，作为备用数据源
    idents = {}
    for ident in (game.get('participantIdentities') or []):
        pid = ident.get('participantId')
        player = ident.get('player') or {}
        if pid is not None:
            idents[pid] = player
    
    # 遍历每个参与者，填充缺失信息
    for p in participants:
        try:
            # 如果已有可读的 summonerName，跳过
            if p.get('summonerName'):
                continue

            info = None
            
            # 方法1: 尝试通过 puuid 查询
            puuid = p.get('puuid') or (p.get('player') or {}).get('puuid')
            if puuid:
                info = get_summoner_by_puuid(token, port, puuid)

            # 方法2: 尝试通过 summonerId 查询
            if not info:
                sid = p.get('summonerId') or (p.get('player') or {}).get('summonerId')
                if sid:
                    info = get_summoner_by_id(token, port, sid)

            # 方法3: 尝试通过 name 查询
            if not info:
                name = p.get('summonerName') or (p.get('player') or {}).get('summonerName')
                if name:
                    info = get_summoner_by_name(token, port, name)

            # 如果查询成功，填充数据
            if info and isinstance(info, dict):
                # 标准化可能的字段名
                p['summonerName'] = (
                    info.get('displayName') or 
                    info.get('summonerName') or 
                    info.get('gameName') or 
                    p.get('summonerName')
                )
                
                # 填充头像ID
                if 'profileIconId' in info:
                    p['profileIcon'] = info.get('profileIconId')
                elif 'profileIcon' in info:
                    p['profileIcon'] = info.get('profileIcon')
                
                # 填充PUUID
                if 'puuid' in info:
                    p['puuid'] = info.get('puuid')
            
            # 备用方案: 使用 participantIdentities 映射
            if (not p.get('summonerName')) and p.get('participantId') and idents.get(p.get('participantId')):
                player = idents.get(p.get('participantId')) or {}
                game_name = (player.get('gameName') or player.get('summonerName')) or ''
                tag = player.get('tagLine')
                
                if game_name:
                    p['summonerName'] = f"{game_name}{('#'+tag) if tag else ''}"
                
                if player.get('profileIcon') is not None and not p.get('profileIcon'):
                    p['profileIcon'] = player.get('profileIcon')
                
                if player.get('puuid') and not p.get('puuid'):
                    p['puuid'] = player.get('puuid')
                    
        except Exception as e:
            print(f"enrich参与者信息失败: {e}")
            continue

    return game
