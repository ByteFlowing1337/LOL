"""
英雄监控服务
自动检测当前选择的英雄，并启用相应的辅助功能
集成OP.GG数据展示
"""
import time
import threading
from lcu_api import get_current_champion_in_game
from config import app_state

# 导入OP.GG API
try:
    from services.opgg_api import get_opgg_api, get_english_champion_name
    OPGG_AVAILABLE = True
except ImportError:
    OPGG_AVAILABLE = False
    print("⚠️ OP.GG API不可用")

class ChampionMonitor:
    """英雄监控器"""
    
    def __init__(self):
        self.current_champion = None
        self.is_monitoring = False
        self.monitor_thread = None
        self.tf_selector = None
        self.callbacks = []
        self.opgg_api = get_opgg_api() if OPGG_AVAILABLE else None
        self.champion_stats_cache = {}  # 缓存英雄数据
        
    def set_tf_selector(self, tf_selector):
        """设置TF选卡器"""
        self.tf_selector = tf_selector
        
    def add_champion_change_callback(self, callback):
        """
        添加英雄改变时的回调函数
        
        Args:
            callback: 回调函数，接收参数 (champion_name, champion_id)
        """
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def remove_champion_change_callback(self, callback):
        """移除回调函数"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def start_monitoring(self):
        """开始监控当前英雄"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("英雄监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        self.current_champion = None
        print("英雄监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 从全局状态获取LCU连接信息
                token = app_state.lcu_credentials.get('auth_token')
                port = app_state.lcu_credentials.get('app_port')
                
                if token and port:
                    # 获取当前英雄
                    champion_info = get_current_champion_in_game(token, port)
                    
                    if champion_info:
                        champion_name = champion_info.get('championName', '')
                        champion_id = champion_info.get('championId', 0)
                        
                        # 如果英雄改变了
                        if champion_name != self.current_champion:
                            self.current_champion = champion_name
                            print(f"检测到英雄改变: {champion_name} (ID: {champion_id})")
                            
                            # 获取OP.GG数据
                            opgg_data = None
                            if self.opgg_api and champion_name:
                                opgg_data = self._get_champion_opgg_data(champion_name)
                                if opgg_data:
                                    print(f"📊 OP.GG数据: Tier={opgg_data.get('tier')}, 胜率={opgg_data.get('win_rate')}%")
                            
                            # 调用所有回调函数
                            for callback in self.callbacks:
                                try:
                                    callback(champion_name, champion_id, opgg_data)
                                except Exception as e:
                                    print(f"回调函数执行错误: {e}")
                            
                            # 如果是卡牌大师，启用TF选卡器
                            if self.tf_selector:
                                if champion_name == 'TwistedFate':
                                    self.tf_selector.set_champion('TwistedFate')
                                    print("卡牌大师已选择，TF选卡器已启用")
                                else:
                                    self.tf_selector.set_champion(None)
                    else:
                        # 没有检测到英雄，可能退出了游戏/选人
                        if self.current_champion:
                            print("未检测到英雄，可能已退出游戏")
                            self.current_champion = None
                            if self.tf_selector:
                                self.tf_selector.set_champion(None)
                
            except Exception as e:
                print(f"英雄监控错误: {e}")
            
            # 每2秒检查一次
            time.sleep(2)
    
    def _get_champion_opgg_data(self, champion_name):
        """
        获取英雄的OP.GG数据（带缓存）
        
        Args:
            champion_name: 英雄名称
        
        Returns:
            dict: OP.GG数据
        """
        # 检查缓存（5分钟有效期）
        if champion_name in self.champion_stats_cache:
            cached_data, cache_time = self.champion_stats_cache[champion_name]
            if time.time() - cache_time < 300:  # 5分钟
                return cached_data
        
        # 获取新数据
        try:
            english_name = get_english_champion_name(champion_name)
            stats = self.opgg_api.get_champion_stats(english_name)
            
            if stats:
                # 缓存数据
                self.champion_stats_cache[champion_name] = (stats, time.time())
                return stats
        except Exception as e:
            print(f"❌ 获取OP.GG数据失败: {e}")
        
        return None

# 全局单例
_champion_monitor = None

def get_champion_monitor():
    """获取全局英雄监控器实例"""
    global _champion_monitor
    if _champion_monitor is None:
        _champion_monitor = ChampionMonitor()
    return _champion_monitor
