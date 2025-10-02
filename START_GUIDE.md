# 启动指南

## 快速开始

### 方式1：使用新版模块化应用（推荐）
```bash
python app_new.py
```

### 方式2：使用旧版应用（备份）
```bash
python app.py
```

### 方式3：测试模块导入
```bash
python test_modules.py
```

## 新旧版本对比

### 旧版 (app.py)
- **文件**: 单一文件 329行
- **优点**: 简单直接
- **缺点**: 难以维护和扩展

### 新版 (app_new.py + 模块)
- **文件**: 模块化结构
  - `config.py` - 配置管理 (50行)
  - `routes/api_routes.py` - HTTP路由 (95行)
  - `services/auto_accept.py` - 自动接受 (40行)
  - `services/auto_analyze.py` - 敌我分析 (130行)
  - `websocket/socket_events.py` - Socket事件 (95行)
  - `utils/network_utils.py` - 工具函数 (30行)
  - `app_new.py` - 主入口 (70行)
- **优点**: 
  - ✅ 结构清晰
  - ✅ 易于维护
  - ✅ 便于测试
  - ✅ 职责分离
  - ✅ 可扩展性强

## 功能验证清单

启动应用后，请验证以下功能：

- [ ] 浏览器自动打开
- [ ] LCU自动连接
- [ ] 点击"自动接受对局"按钮
- [ ] 点击"敌我分析"按钮
- [ ] ChampSelect阶段显示队友战绩
- [ ] InProgress阶段显示敌人战绩
- [ ] 手动战绩查询功能

## 迁移步骤

如果新版测试通过，可以完成迁移：

1. 备份旧版
```bash
mv app.py app_old.py.bak
```

2. 启用新版
```bash
mv app_new.py app.py
```

3. 删除备份（可选）
```bash
rm app_old.py.bak
```

## 故障排查

### 问题1: 模块导入错误
**解决**: 运行 `python test_modules.py` 检查

### 问题2: 功能异常
**解决**: 查看控制台日志，对比旧版行为

### 问题3: LCU连接失败
**解决**: 确保英雄联盟客户端正在运行
