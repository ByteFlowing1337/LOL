"""
LOL游戏内存读取模块
使用 pymem 读取游戏进程内存，获取实时游戏数据

功能:
- 读取当前英雄位置、血量、蓝量
- 读取敌方英雄位置
- 读取技能冷却时间
- 读取金币、等级等信息

注意:
- 需要管理员权限运行
- 游戏更新后，内存地址可能改变
"""
import pymem
import pymem.process
from pymem import Pymem
import struct
import time
from threading import Thread, Lock
from typing import Optional, Dict, List
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemoryOffsets:
    """
    内存偏移地址配置
    注意: 这些地址需要根据游戏版本更新
    可以使用 Cheat Engine 等工具找到正确的偏移
    """
    # 基础地址偏移
    GAME_TIME = 0x31A0D90  # 游戏时间
    LOCAL_PLAYER = 0x31A2DD8  # 本地玩家基址
    
    # 英雄对象偏移
    OBJECT_MANAGER = 0x18CAC00  # 对象管理器
    
    # 英雄属性偏移（相对于英雄对象）
    POSITION_X = 0x1D8  # X坐标
    POSITION_Y = 0x1DC  # Y坐标 (高度)
    POSITION_Z = 0x1E0  # Z坐标
    
    HEALTH = 0xD98  # 当前生命值
    MAX_HEALTH = 0xDA8  # 最大生命值
    MANA = 0x298  # 当前法力值
    MAX_MANA = 0x2A8  # 最大法力值
    
    CHAMPION_NAME = 0x2DB4  # 英雄名称
    LEVEL = 0x33BC  # 等级
    GOLD = 0x1BA0  # 金币
    
    # 技能CD偏移
    SPELL_Q_CD = 0x1234  # Q技能CD
    SPELL_W_CD = 0x1238  # W技能CD
    SPELL_E_CD = 0x123C  # E技能CD
    SPELL_R_CD = 0x1240  # R技能CD
    
    # 队伍标识
    TEAM = 0x34  # 队伍 (100=蓝色方, 200=红色方)
    IS_ALIVE = 0x274  # 是否存活


class LOLMemoryReader:
    """LOL游戏内存读取器"""
    
    def __init__(self):
        self.pm: Optional[Pymem] = None
        self.base_address: Optional[int] = None
        self.is_connected = False
        self.lock = Lock()
        
        # 缓存数据
        self.local_player_data = {}
        self.enemy_data = []
        self.teammate_data = []
        
        # 自动更新线程
        self.auto_update_thread = None
        self.is_running = False
        
    def connect(self) -> bool:
        """
        连接到LOL游戏进程
        
        Returns:
            bool: 是否连接成功
        """
        try:
            # 检查是否有管理员权限
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                logger.error("❌ 需要管理员权限！")
                logger.error("   请右键程序 → 以管理员身份运行")
                return False
            
            # 尝试连接到League of Legends进程
            process_names = [
                "League of Legends.exe",
                "LeagueClient.exe"
            ]
            
            for process_name in process_names:
                try:
                    logger.info(f"🔍 尝试连接到: {process_name}")
                    
                    # 使用更兼容的方式打开进程
                    self.pm = Pymem(process_name)
                    
                    # 尝试获取基址，使用备用方法
                    try:
                        self.base_address = self.pm.base_address
                    except:
                        # 如果获取基址失败，使用进程基址
                        logger.warning("   ⚠️ 无法获取模块基址，使用进程基址")
                        self.base_address = self.pm.process_base.lpBaseOfDll
                    
                    self.is_connected = True
                    logger.info(f"✅ 成功连接到进程: {process_name}")
                    logger.info(f"📍 进程ID: {self.pm.process_id}")
                    logger.info(f"📍 基址: 0x{self.base_address:X}")
                    return True
                    
                except pymem.exception.ProcessNotFound:
                    logger.debug(f"   进程 {process_name} 未找到")
                    continue
                    
                except pymem.exception.CouldNotOpenProcess as e:
                    error_code = str(e).split(':')[-1].strip()
                    if '5' in error_code or '2500' in error_code:
                        logger.error(f"❌ 访问被拒绝 (错误代码: {error_code})")
                        logger.error("   原因: 需要管理员权限")
                        logger.error("   解决方法:")
                        logger.error("   1. 关闭当前程序")
                        logger.error("   2. 右键程序 → 以管理员身份运行")
                        logger.error("   3. 重新尝试连接")
                    else:
                        logger.error(f"❌ 无法打开进程: {e}")
                    return False
                    
                except pymem.exception.ProcessError as e:
                    error_msg = str(e)
                    if "first module" in error_msg.lower():
                        logger.error(f"❌ 进程模块访问失败: {process_name}")
                        logger.error("   可能原因:")
                        logger.error("   1. 游戏使用了反调试保护")
                        logger.error("   2. 进程架构不匹配（32位/64位）")
                        logger.error("   3. 游戏正在启动中，请稍后重试")
                        logger.error("")
                        logger.error("   建议:")
                        logger.error("   - 等待游戏完全加载后再连接")
                        logger.error("   - 尝试在对局中连接")
                        logger.error("   - 检查是否使用64位Python")
                    else:
                        logger.error(f"❌ 进程错误: {e}")
                    continue
                    
            logger.error("❌ 未找到可用的LOL游戏进程")
            logger.error("")
            logger.error("   支持的进程:")
            for name in process_names:
                logger.error(f"   - {name}")
            logger.error("")
            logger.error("   请确保:")
            logger.error("   1. 游戏正在运行（最好已进入对局）")
            logger.error("   2. 使用64位Python")
            logger.error("   3. 游戏完全加载完成")
            return False
            
        except Exception as e:
            logger.error(f"❌ 连接游戏进程失败: {e}")
            logger.error(f"   错误类型: {type(e).__name__}")
            return False
    
    def disconnect(self):
        """断开连接"""
        self.is_connected = False
        if self.pm:
            self.pm.close_process()
            self.pm = None
        logger.info("断开游戏进程连接")
    
    def read_int(self, address: int) -> int:
        """读取整数"""
        try:
            return self.pm.read_int(address)
        except:
            return 0
    
    def read_float(self, address: int) -> float:
        """读取浮点数"""
        try:
            return self.pm.read_float(address)
        except:
            return 0.0
    
    def read_bool(self, address: int) -> bool:
        """读取布尔值"""
        try:
            return self.pm.read_bool(address)
        except:
            return False
    
    def read_string(self, address: int, length: int = 32) -> str:
        """读取字符串"""
        try:
            return self.pm.read_string(address, length)
        except:
            return ""
    
    def read_pointer(self, base: int, offsets: List[int]) -> int:
        """
        读取指针链
        
        Args:
            base: 基址
            offsets: 偏移列表
            
        Returns:
            int: 最终地址
        """
        address = base
        try:
            for offset in offsets[:-1]:
                address = self.pm.read_int(address + offset)
            return address + offsets[-1]
        except:
            return 0
    
    def get_local_player_address(self) -> int:
        """获取本地玩家地址"""
        if not self.is_connected or not self.base_address:
            return 0
        
        try:
            return self.pm.read_int(self.base_address + MemoryOffsets.LOCAL_PLAYER)
        except:
            return 0
    
    def get_local_player_data(self) -> Dict:
        """
        获取本地玩家数据
        
        Returns:
            dict: 玩家数据字典
        """
        if not self.is_connected:
            return {}
        
        player_addr = self.get_local_player_address()
        if not player_addr:
            return {}
        
        try:
            data = {
                'position': {
                    'x': self.read_float(player_addr + MemoryOffsets.POSITION_X),
                    'y': self.read_float(player_addr + MemoryOffsets.POSITION_Y),
                    'z': self.read_float(player_addr + MemoryOffsets.POSITION_Z),
                },
                'health': {
                    'current': self.read_float(player_addr + MemoryOffsets.HEALTH),
                    'max': self.read_float(player_addr + MemoryOffsets.MAX_HEALTH),
                },
                'mana': {
                    'current': self.read_float(player_addr + MemoryOffsets.MANA),
                    'max': self.read_float(player_addr + MemoryOffsets.MAX_MANA),
                },
                'level': self.read_int(player_addr + MemoryOffsets.LEVEL),
                'gold': self.read_float(player_addr + MemoryOffsets.GOLD),
                'team': self.read_int(player_addr + MemoryOffsets.TEAM),
                'is_alive': self.read_bool(player_addr + MemoryOffsets.IS_ALIVE),
            }
            
            # 计算百分比
            if data['health']['max'] > 0:
                data['health']['percent'] = (data['health']['current'] / data['health']['max']) * 100
            else:
                data['health']['percent'] = 0
                
            if data['mana']['max'] > 0:
                data['mana']['percent'] = (data['mana']['current'] / data['mana']['max']) * 100
            else:
                data['mana']['percent'] = 0
            
            with self.lock:
                self.local_player_data = data
            
            return data
            
        except Exception as e:
            logger.error(f"读取玩家数据失败: {e}")
            return {}
    
    def get_spell_cooldowns(self) -> Dict:
        """
        获取技能冷却时间
        
        Returns:
            dict: 技能CD字典
        """
        if not self.is_connected:
            return {}
        
        player_addr = self.get_local_player_address()
        if not player_addr:
            return {}
        
        try:
            return {
                'Q': self.read_float(player_addr + MemoryOffsets.SPELL_Q_CD),
                'W': self.read_float(player_addr + MemoryOffsets.SPELL_W_CD),
                'E': self.read_float(player_addr + MemoryOffsets.SPELL_E_CD),
                'R': self.read_float(player_addr + MemoryOffsets.SPELL_R_CD),
            }
        except:
            return {}
    
    def get_game_time(self) -> float:
        """
        获取游戏时间
        
        Returns:
            float: 游戏时间（秒）
        """
        if not self.is_connected or not self.base_address:
            return 0.0
        
        try:
            return self.read_float(self.base_address + MemoryOffsets.GAME_TIME)
        except:
            return 0.0
    
    def get_all_champions(self) -> List[Dict]:
        """
        获取所有英雄对象（包括队友和敌人）
        注意: 这个功能需要遍历对象管理器，相对复杂
        
        Returns:
            list: 英雄数据列表
        """
        # TODO: 实现对象管理器遍历
        # 这需要更深入的逆向工程来找到对象列表结构
        return []
    
    def start_auto_update(self, interval: float = 0.1):
        """
        启动自动更新线程
        
        Args:
            interval: 更新间隔（秒）
        """
        if self.is_running:
            return
        
        self.is_running = True
        self.auto_update_thread = Thread(target=self._auto_update_loop, args=(interval,), daemon=True)
        self.auto_update_thread.start()
        logger.info(f"🚀 启动自动更新线程，间隔: {interval}秒")
    
    def stop_auto_update(self):
        """停止自动更新"""
        self.is_running = False
        if self.auto_update_thread:
            self.auto_update_thread.join(timeout=2)
        logger.info("停止自动更新线程")
    
    def _auto_update_loop(self, interval: float):
        """自动更新循环"""
        while self.is_running:
            try:
                if self.is_connected:
                    self.get_local_player_data()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"自动更新错误: {e}")
                time.sleep(1)
    
    def get_cached_data(self) -> Dict:
        """
        获取缓存的数据（线程安全）
        
        Returns:
            dict: 包含所有缓存数据
        """
        with self.lock:
            return {
                'local_player': self.local_player_data.copy(),
                'game_time': self.get_game_time(),
                'is_connected': self.is_connected,
            }


# 全局实例
_memory_reader = None


def get_memory_reader() -> LOLMemoryReader:
    """
    获取全局内存读取器实例
    
    Returns:
        LOLMemoryReader: 内存读取器实例
    """
    global _memory_reader
    if _memory_reader is None:
        _memory_reader = LOLMemoryReader()
    return _memory_reader


# 测试代码
if __name__ == '__main__':
    print("="*60)
    print("  LOL 内存读取测试")
    print("="*60)
    print()
    
    reader = get_memory_reader()
    
    # 连接游戏
    print("🔌 正在连接游戏进程...")
    if reader.connect():
        print("✅ 连接成功！")
        print()
        
        # 启动自动更新
        reader.start_auto_update(interval=1.0)
        
        try:
            # 持续读取数据
            for i in range(10):
                print(f"\n📊 数据更新 #{i+1}")
                print("-" * 60)
                
                # 获取玩家数据
                player_data = reader.get_local_player_data()
                if player_data:
                    print(f"位置: ({player_data['position']['x']:.2f}, "
                          f"{player_data['position']['y']:.2f}, "
                          f"{player_data['position']['z']:.2f})")
                    print(f"生命值: {player_data['health']['current']:.0f} / "
                          f"{player_data['health']['max']:.0f} "
                          f"({player_data['health']['percent']:.1f}%)")
                    print(f"法力值: {player_data['mana']['current']:.0f} / "
                          f"{player_data['mana']['max']:.0f} "
                          f"({player_data['mana']['percent']:.1f}%)")
                    print(f"等级: {player_data['level']}")
                    print(f"金币: {player_data['gold']:.0f}")
                    print(f"队伍: {'蓝色方' if player_data['team'] == 100 else '红色方'}")
                    print(f"存活: {'是' if player_data['is_alive'] else '否'}")
                
                # 获取游戏时间
                game_time = reader.get_game_time()
                minutes = int(game_time // 60)
                seconds = int(game_time % 60)
                print(f"游戏时间: {minutes:02d}:{seconds:02d}")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  停止测试")
        finally:
            reader.stop_auto_update()
            reader.disconnect()
            
    else:
        print("❌ 连接失败！")
        print("\n可能的原因:")
        print("1. 游戏未运行")
        print("2. 需要管理员权限")
        print("3. 进程名称不匹配")
    
    print("\n" + "="*60)
