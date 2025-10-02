"""
YOLO模型训练脚本
用于训练LOL专用的YOLO检测模型

使用前提:
1. 已收集并标注好训练数据
2. 数据集格式为YOLO格式
3. 已创建dataset.yaml配置文件

使用方法:
python tools/train_yolo_model.py
"""

import os
from pathlib import Path
from ultralytics import YOLO
import torch


def check_requirements():
    """检查环境要求"""
    print("=" * 60)
    print("🔍 检查训练环境")
    print("=" * 60)
    
    # 检查CUDA
    cuda_available = torch.cuda.is_available()
    if cuda_available:
        print(f"✅ GPU可用: {torch.cuda.get_device_name(0)}")
        print(f"   CUDA版本: {torch.version.cuda}")
        print(f"   显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        device = 'cuda'
    else:
        print("⚠️  未检测到GPU，将使用CPU训练")
        print("   提示: GPU训练速度快10-50倍")
        device = 'cpu'
    
    print()
    return device


def create_dataset_yaml():
    """创建数据集配置文件模板"""
    yaml_path = Path("training_data/dataset.yaml")
    
    if yaml_path.exists():
        print(f"✅ 数据集配置已存在: {yaml_path}")
        return yaml_path
    
    yaml_content = """# LOL YOLO数据集配置
path: ./training_data  # 数据集根目录
train: images/train    # 训练集图片目录
val: images/val        # 验证集图片目录
test: images/test      # 测试集图片目录（可选）

# 类别数量
nc: 8

# 类别名称
names:
  0: champion_casting      # 英雄抬手/施法
  1: enemy_champion        # 敌方英雄
  2: ally_champion         # 友方英雄
  3: skillshot_indicator   # 技能指示器
  4: danger_ping           # 危险信号
  5: objective_spawn       # 目标刷新
  6: low_health            # 低血量
  7: enemy_ward            # 敌方眼位
"""
    
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    yaml_path.write_text(yaml_content, encoding='utf-8')
    
    print(f"✅ 创建数据集配置: {yaml_path}")
    print("⚠️  请根据实际情况修改路径配置")
    
    return yaml_path


def train_model(device='cpu', epochs=100, batch=16, imgsz=640):
    """
    训练YOLO模型
    
    Args:
        device: 训练设备 ('cpu' 或 'cuda')
        epochs: 训练轮数
        batch: 批次大小
        imgsz: 图像尺寸
    """
    print("=" * 60)
    print("🚀 开始训练YOLO模型")
    print("=" * 60)
    
    # 检查数据集配置
    dataset_yaml = Path("training_data/dataset.yaml")
    if not dataset_yaml.exists():
        print(f"❌ 数据集配置文件不存在: {dataset_yaml}")
        print("💡 请先创建dataset.yaml配置文件")
        return False
    
    # 检查训练数据
    train_dir = Path("training_data/images/train")
    if not train_dir.exists() or not list(train_dir.glob("*.jpg")):
        print(f"❌ 训练数据不存在: {train_dir}")
        print("💡 请先使用collect_training_data.py收集并标注数据")
        return False
    
    print(f"📁 数据集配置: {dataset_yaml}")
    print(f"🖼️  训练图片数: {len(list(train_dir.glob('*.jpg')))}")
    print(f"🎯 训练设备: {device}")
    print(f"📊 训练参数:")
    print(f"   - Epochs: {epochs}")
    print(f"   - Batch: {batch}")
    print(f"   - Image size: {imgsz}")
    print()
    
    try:
        # 加载预训练模型
        print("📦 加载YOLOv8预训练模型...")
        model = YOLO('yolov8n.pt')
        
        # 训练模型
        print("🏋️ 开始训练...")
        results = model.train(
            data=str(dataset_yaml),
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            device=device,
            name='lol_yolo',
            patience=20,          # 早停耐心值
            save=True,            # 保存检查点
            plots=True,           # 生成训练图表
            val=True,             # 每轮验证
            workers=4,            # 数据加载线程数
            project='runs/train', # 输出目录
        )
        
        print()
        print("=" * 60)
        print("✅ 训练完成！")
        print("=" * 60)
        
        # 复制最佳模型到models目录
        best_model = Path("runs/train/lol_yolo/weights/best.pt")
        if best_model.exists():
            output_path = Path("models/lol_yolo.pt")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.copy(best_model, output_path)
            
            print(f"📦 最佳模型已保存: {output_path.absolute()}")
            print()
            print("🎯 模型信息:")
            print(f"   - 训练轮数: {epochs}")
            print(f"   - 验证mAP: 查看 runs/train/lol_yolo/results.png")
            print(f"   - 模型大小: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
            print()
            print("📈 训练结果:")
            print(f"   - 结果图表: runs/train/lol_yolo/")
            print(f"   - 混淆矩阵: runs/train/lol_yolo/confusion_matrix.png")
            print(f"   - 训练曲线: runs/train/lol_yolo/results.png")
            print()
            print("🚀 下一步:")
            print("  1. 查看训练结果图表评估模型质量")
            print("  2. 重启应用: python app_new.py")
            print("  3. 测试检测效果: http://localhost:5000/vision_detection")
            print("  4. 如果效果不佳，增加训练数据或调整参数")
        else:
            print("⚠️  未找到训练好的模型文件")
        
        return True
        
    except Exception as e:
        print(f"❌ 训练失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print()
    print("🎓 LOL YOLO模型训练工具")
    print()
    
    # 检查环境
    device = check_requirements()
    print()
    
    # 创建数据集配置（如果不存在）
    create_dataset_yaml()
    print()
    
    # 训练参数
    print("=" * 60)
    print("⚙️  训练参数配置")
    print("=" * 60)
    print()
    print("推荐配置:")
    print("  - 快速测试: epochs=50, batch=16")
    print("  - 标准训练: epochs=100, batch=8")
    print("  - 高质量: epochs=200, batch=4")
    print()
    
    # 获取用户输入
    try:
        epochs_input = input("训练轮数 [默认100]: ").strip()
        epochs = int(epochs_input) if epochs_input else 100
        
        batch_input = input("批次大小 [默认8]: ").strip()
        batch = int(batch_input) if batch_input else 8
        
        print()
        
        # 开始训练
        success = train_model(device=device, epochs=epochs, batch=batch)
        
        if not success:
            print()
            print("=" * 60)
            print("❌ 训练失败")
            print("=" * 60)
            print()
            print("💡 故障排除:")
            print("  1. 确认数据集目录结构正确")
            print("  2. 确认图片和标签文件配对")
            print("  3. 检查dataset.yaml配置")
            print("  4. 查看完整错误信息")
            print()
            print("📚 参考文档: models/README.md")
            
    except KeyboardInterrupt:
        print()
        print("⚠️  训练被用户中断")
    except Exception as e:
        print(f"❌ 发生错误: {e}")


if __name__ == '__main__':
    main()
