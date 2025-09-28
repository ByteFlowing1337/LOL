import requests
from requests.auth import HTTPBasicAuth
from typing import Optional, Dict

def fetch_puuid(
    app_port: int, 
    auth_token: str, 
    summoner_name: str
) -> Optional[str]:
    """
    通过英雄联盟客户端 API (LCU) 查询并获取指定召唤师的 PUUID。

    参数:
    - app_port (int): LCU 客户端正在监听的端口号。
    - auth_token (str): LCU 客户端的认证令牌 (Secret Key)。
    - summoner_name (str): 要查询的召唤师名称。

    返回:
    - Optional[str]: 成功则返回 PUUID 字符串，失败则返回 None。
    """
    
    # LCU 的基础地址，PUUID 查询不需要将 auth_token 放在 URL 中，
    # 但为了兼容性和明确性，我们使用 auth 参数
    base_url = f"https://127.0.0.1:{app_port}"
    endpoint = "/lol-summoner/v1/summoners"
    url = base_url + endpoint

    try:
        # 发送 GET 请求
        response = requests.get(
            url,
            # 使用 params 传递查询参数，即召唤师名称
            params={'name': summoner_name},
            # 使用 HTTPBasicAuth 传递认证信息
            auth=HTTPBasicAuth('riot', auth_token),
            # LCU 使用自签名证书，必须禁用 SSL 验证
            verify=False,
            timeout=10
        )
        
        # 检查响应状态码
        if response.status_code == 200:
            data: Dict = response.json()
            # 从响应数据中提取 PUUID 字段
            return data.get('puuid')
        else:
            # 请求失败的详细信息（您可以选择性地打印或记录）
            print(f"ERROR: 获取PUUID失败! 状态码: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        # 捕获网络连接或超时等异常
        print(f"ERROR: 请求异常: {e}")
        return None

# --- 使用示例 ---
# 假设您已通过其他方式获取了 LCU 的端口和令牌
LCU_PORT = 62351 
LCU_TOKEN = "uGuzzl0sY7gas6xQfffV3A"
SUMMONER = "召唤师2321#55777"

puuid = fetch_puuid(LCU_PORT, LCU_TOKEN, SUMMONER)

if puuid:
     print(f"找到召唤师 {SUMMONER} 的 PUUID: {puuid}")
else:
    print(f"未找到召唤师 {SUMMONER} 的 PUUID 或请求失败。")