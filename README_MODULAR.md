# LOLHelper WebUI - 模块化版本

## 项目结构

```
LOLHelperWeb/
├── app.py                      # 旧版主文件（保留备份）
├── app_new.py                  # 新版主入口文件
├── config.py                   # 全局配置和状态管理
├── lcu_api.py                 # LCU API封装
├── constants.py               # 常量定义
│
├── routes/                    # 路由模块
│   ├── __init__.py
│   └── api_routes.py          # HTTP API路由
│
├── services/                  # 业务逻辑服务
│   ├── __init__.py
│   ├── auto_accept.py         # 自动接受对局服务
│   └── auto_analyze.py        # 敌我分析服务
│
├── utils/                     # 工具模块
│   ├── __init__.py
│   └── network_utils.py       # 网络工具
│
├── websocket/                 # WebSocket事件处理
│   ├── __init__.py
│   └── socket_events.py       # Socket事件注册
│
├── static/                    # 静态资源
│   └── js/
│       └── main.js
│
└── templates/                 # HTML模板
    └── index.html
```

## 模块说明

### 1. config.py - 配置管理
- 存储应用配置（密钥、主机、端口）
- 管理全局状态（AppState类）
- 提供LCU连接状态、分析状态等

### 2. routes/api_routes.py - HTTP路由
- 处理HTTP请求
- 提供战绩查询API
- 使用Flask Blueprint组织路由

### 3. services/ - 业务逻辑
- **auto_accept.py**: 自动接受对局的后台任务
- **auto_analyze.py**: 敌我分析的后台任务（ChampSelect + InProgress）

### 4. websocket/socket_events.py - WebSocket
- 处理前端连接
- 注册Socket.IO事件监听器
- 启动/停止后台服务

### 5. utils/network_utils.py - 工具函数
- 获取本地IP地址
- 其他网络相关工具

## 使用方法

### 启动新版应用
```bash
python app_new.py
```

### 启动旧版应用（备份）
```bash
python app.py
```

## 代码改进

### 优势
1. ✅ **模块化**: 按功能拆分，易于维护
2. ✅ **可扩展**: 新增功能只需添加新模块
3. ✅ **可测试**: 每个模块可独立测试
4. ✅ **清晰结构**: 代码组织更合理
5. ✅ **职责分离**: 路由、服务、工具各司其职

### 对比
| 特性 | 旧版 (app.py) | 新版 (模块化) |
|------|---------------|---------------|
| 文件数量 | 1个主文件 | 多个模块文件 |
| 代码行数 | 329行 | 分散到多个文件 |
| 可维护性 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 可扩展性 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 可测试性 | ⭐⭐ | ⭐⭐⭐⭐⭐ |

## 功能不变
- 自动接受对局 ✅
- ChampSelect阶段分析队友 ✅
- InProgress阶段分析敌人 ✅
- 战绩查询API ✅
- WebSocket实时通信 ✅

## 下一步
1. 测试新版应用是否正常工作
2. 确认无误后可删除 `app.py`（旧版）
3. 将 `app_new.py` 重命名为 `app.py`
