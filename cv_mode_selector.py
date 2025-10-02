"""
CV检测模式管理
提供传统CV和YOLO两种模式的切换和管理
"""
from enum import Enum


class CVDetectionMode(Enum):
    """CV检测模式枚举"""
    TRADITIONAL = "traditional"  # 传统CV模式（OpenCV图像处理）
    YOLO = "yolo"               # YOLO深度学习模式
    HYBRID = "hybrid"           # 混合模式（两种方法结合）


class CVModeConfig:
    """CV模式配置类"""
    
    def __init__(self, mode=CVDetectionMode.TRADITIONAL):
        """
        初始化CV模式配置
        
        Args:
            mode: CV检测模式（默认为传统CV）
        """
        self.mode = mode
        self.config = self._get_mode_config()
    
    def _get_mode_config(self):
        """获取当前模式的配置"""
        configs = {
            CVDetectionMode.TRADITIONAL: {
                'name': '传统CV模式',
                'description': '基于OpenCV的图像处理检测，无需训练模型',
                'features': [
                    '小地图敌人检测（红色标记识别）',
                    '血量状态检测（颜色比例分析）',
                    '危险信号检测（形状匹配）',
                    '技能冷却检测（亮度分析）'
                ],
                'advantages': [
                    '⚡ 速度极快（~50ms）',
                    '📦 无需模型文件',
                    '💻 CPU占用低（5-10%）',
                    '🎯 固定UI检测准确',
                    '✅ 立即可用'
                ],
                'limitations': [
                    '❌ 无法检测复杂动作',
                    '❌ 对光照变化敏感',
                    '❌ 需要调整颜色参数'
                ],
                'use_cases': [
                    '快速获取小地图信息',
                    '实时监控血量和技能',
                    '资源受限的设备',
                    '不需要深度分析'
                ]
            },
            
            CVDetectionMode.YOLO: {
                'name': 'YOLO深度学习模式',
                'description': '基于YOLO神经网络的目标检测，需要训练模型',
                'features': [
                    '英雄施法动作检测',
                    '技能指示器识别',
                    '复杂场景理解',
                    '多目标同时检测'
                ],
                'advantages': [
                    '🎯 检测准确度高（95%+）',
                    '🔍 可识别复杂动作',
                    '💪 鲁棒性强',
                    '📈 可持续训练改进',
                    '🌟 适应性强'
                ],
                'limitations': [
                    '⏱️ 速度较慢（~300ms）',
                    '📦 需要模型文件（~100MB）',
                    '💻 CPU/GPU占用高（30-50%）',
                    '📊 需要训练数据',
                    '⚙️ 配置复杂'
                ],
                'use_cases': [
                    '精确识别英雄动作',
                    '分析游戏录像',
                    '训练AI助手',
                    '高精度需求场景'
                ]
            },
            
            CVDetectionMode.HYBRID: {
                'name': '混合模式',
                'description': '结合传统CV和YOLO的优势，智能分配检测任务',
                'features': [
                    '传统CV检测固定UI（小地图、血条等）',
                    'YOLO检测动态内容（英雄动作等）',
                    '智能任务分配',
                    '性能优化'
                ],
                'advantages': [
                    '🚀 性能均衡（~200ms）',
                    '🎯 准确度高',
                    '💡 各取所长',
                    '⚖️ 资源占用适中',
                    '✨ 推荐使用'
                ],
                'limitations': [
                    '⚙️ 需要两套系统',
                    '🔧 配置稍复杂'
                ],
                'use_cases': [
                    '日常游戏使用',
                    '实时辅助',
                    '平衡性能和准确度',
                    '推荐默认模式'
                ]
            }
        }
        
        return configs.get(self.mode, configs[CVDetectionMode.TRADITIONAL])
    
    def print_info(self):
        """打印当前模式信息"""
        print("\n" + "=" * 70)
        print(f"📋 {self.config['name']}")
        print("=" * 70)
        print(f"\n📝 描述: {self.config['description']}")
        
        print("\n✨ 功能:")
        for feature in self.config['features']:
            print(f"   • {feature}")
        
        print("\n✅ 优势:")
        for advantage in self.config['advantages']:
            print(f"   {advantage}")
        
        print("\n⚠️ 限制:")
        for limitation in self.config['limitations']:
            print(f"   {limitation}")
        
        print("\n🎯 适用场景:")
        for use_case in self.config['use_cases']:
            print(f"   • {use_case}")
        
        print("=" * 70 + "\n")
    
    def switch_mode(self, new_mode):
        """
        切换检测模式
        
        Args:
            new_mode: 新的检测模式
        """
        if not isinstance(new_mode, CVDetectionMode):
            raise ValueError(f"无效的模式: {new_mode}")
        
        old_mode = self.mode
        self.mode = new_mode
        self.config = self._get_mode_config()
        
        print(f"\n✅ 检测模式已切换: {old_mode.value} → {new_mode.value}")
        self.print_info()


def compare_modes():
    """对比三种检测模式"""
    print("\n" + "=" * 70)
    print("📊 CV检测模式对比")
    print("=" * 70)
    
    comparison = """
┌─────────────┬──────────────┬──────────────┬──────────────┐
│   对比项    │   传统CV     │     YOLO     │   混合模式   │
├─────────────┼──────────────┼──────────────┼──────────────┤
│ 检测速度    │   ⚡⚡⚡⚡⚡   │     ⚡⚡     │    ⚡⚡⚡⚡   │
│             │    ~50ms     │   ~300ms     │   ~200ms     │
├─────────────┼──────────────┼──────────────┼──────────────┤
│ 准确度      │    ⭐⭐⭐    │   ⭐⭐⭐⭐⭐  │   ⭐⭐⭐⭐⭐  │
│             │    80-85%    │    95%+      │    90-95%    │
├─────────────┼──────────────┼──────────────┼──────────────┤
│ CPU占用     │   💻💻      │   💻💻💻💻   │   💻💻💻    │
│             │    5-10%     │   30-50%     │   15-25%     │
├─────────────┼──────────────┼──────────────┼──────────────┤
│ 模型需求    │      无      │     必需     │   可选/必需  │
│             │      0MB     │   ~100MB     │   ~100MB     │
├─────────────┼──────────────┼──────────────┼──────────────┤
│ 训练数据    │      无      │     必需     │   可选/必需  │
│             │   立即可用   │   需标注     │  部分需要    │
├─────────────┼──────────────┼──────────────┼──────────────┤
│ 检测能力    │   基础UI     │   全面识别   │  全面识别    │
│             │  小地图血条  │ 动作+UI+场景 │ 动作+UI+场景 │
├─────────────┼──────────────┼──────────────┼──────────────┤
│ 适用场景    │  快速测试    │  高精度需求  │  日常使用    │
│             │  资源受限    │  离线分析    │  推荐默认    │
└─────────────┴──────────────┴──────────────┴──────────────┘
"""
    print(comparison)
    
    print("\n💡 推荐选择:")
    print("   • 🚀 刚开始使用: 传统CV模式（立即可用）")
    print("   • 🎯 追求精度: YOLO模式（需训练模型）")
    print("   • ✨ 日常使用: 混合模式（最佳平衡）")
    print("=" * 70 + "\n")


def get_mode_selector():
    """交互式模式选择器"""
    print("\n" + "=" * 70)
    print("🎮 CV检测模式选择")
    print("=" * 70)
    
    print("\n请选择检测模式:")
    print("  1. 传统CV模式 ⚡ (推荐新手)")
    print("  2. YOLO模式 🎯")
    print("  3. 混合模式 🚀 (推荐)")
    print("  4. 查看模式对比")
    print("  0. 退出")
    
    while True:
        choice = input("\n请输入选项 (0-4): ").strip()
        
        if choice == '0':
            print("👋 退出模式选择")
            return None
        elif choice == '1':
            return CVDetectionMode.TRADITIONAL
        elif choice == '2':
            return CVDetectionMode.YOLO
        elif choice == '3':
            return CVDetectionMode.HYBRID
        elif choice == '4':
            compare_modes()
        else:
            print("❌ 无效选项，请重新输入")


if __name__ == "__main__":
    # 演示模式配置
    print("🎮 CV检测模式管理系统")
    
    # 1. 展示所有模式
    for mode in CVDetectionMode:
        config = CVModeConfig(mode)
        config.print_info()
    
    # 2. 对比模式
    compare_modes()
    
    # 3. 交互式选择
    selected_mode = get_mode_selector()
    if selected_mode:
        config = CVModeConfig(selected_mode)
        print(f"\n✅ 您选择了: {config.config['name']}")
        config.print_info()
