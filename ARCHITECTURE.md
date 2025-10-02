# LOLHelper WebUI 架构图

## 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 (Browser)                           │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  index.html  │  │   main.js    │  │  Socket.IO   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ HTTP / WebSocket
                            │
┌───────────────────────────┴─────────────────────────────────────┐
│                      后端 (Flask + SocketIO)                     │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    app_new.py (主入口)                   │   │
│  │  - create_app()                                          │   │
│  │  - 注册蓝图、WebSocket事件                              │   │
│  └────────────┬──────────────────┬─────────────────────────┘   │
│               │                  │                               │
│  ┌────────────▼──────┐  ┌───────▼──────────┐                   │
│  │   routes/         │  │   websocket/     │                   │
│  │   api_routes.py   │  │   socket_events.py│                  │
│  │  - GET /          │  │  - connect       │                   │
│  │  - GET /history   │  │  - start_accept  │                   │
│  └────────────┬──────┘  │  - start_analyze │                   │
│               │          └───────┬──────────┘                   │
│               │                  │                               │
│  ┌────────────▼──────────────────▼─────────────────────────┐   │
│  │                     config.py (状态管理)                 │   │
│  │                       AppState                           │   │
│  │  - lcu_credentials                                       │   │
│  │  - auto_accept_enabled                                   │   │
│  │  - auto_analyze_enabled                                  │   │
│  │  - teammate_analysis_done                                │   │
│  │  - enemy_analysis_done                                   │   │
│  │  - current_teammates                                     │   │
│  └─────────────┬────────────────────────────────────────────┘   │
│                │                                                 │
│  ┌─────────────▼──────────────────────┐                        │
│  │         services/                  │                        │
│  │                                    │                        │
│  │  ┌──────────────────────────────┐ │                        │
│  │  │  auto_accept.py              │ │                        │
│  │  │  - auto_accept_task()        │ │                        │
│  │  │    └─> ReadyCheck 阶段       │ │                        │
│  │  └──────────────────────────────┘ │                        │
│  │                                    │                        │
│  │  ┌──────────────────────────────┐ │                        │
│  │  │  auto_analyze.py             │ │                        │
│  │  │  - auto_analyze_task()       │ │                        │
│  │  │  - _analyze_teammates()      │ │                        │
│  │  │    └─> ChampSelect 阶段      │ │                        │
│  │  │  - _analyze_enemies()        │ │                        │
│  │  │    └─> InProgress 阶段       │ │                        │
│  │  └──────────────────────────────┘ │                        │
│  └─────────────┬──────────────────────┘                        │
│                │                                                 │
│  ┌─────────────▼──────────────────────┐                        │
│  │         lcu_api.py                 │                        │
│  │  - autodetect_credentials()        │                        │
│  │  - get_gameflow_phase()            │                        │
│  │  - accept_ready_check()            │                        │
│  │  - get_champ_select_session()      │                        │
│  │  - get_all_players_from_game()     │                        │
│  │  - get_puuid()                     │                        │
│  │  - get_match_history()             │                        │
│  └────────────────────────────────────┘                        │
└───────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS (端口 2999, 动态端口)
                            │
┌───────────────────────────┴─────────────────────────────────────┐
│                    League of Legends Client                      │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │  LCU API         │  │  Game API        │                    │
│  │  (动态端口)      │  │  (端口 2999)     │                    │
│  │  - 游戏状态      │  │  - 实时游戏数据  │                    │
│  │  - 选人会话      │  │  - 所有玩家信息  │                    │
│  │  - 战绩查询      │  │                  │                    │
│  └──────────────────┘  └──────────────────┘                    │
└───────────────────────────────────────────────────────────────┘
```

## 数据流示例

### 1. 自动接受对局
```
用户点击"自动接受对局"按钮
    ↓
前端 Socket.IO emit 'start_auto_accept'
    ↓
websocket/socket_events.py 处理事件
    ↓
启动 services/auto_accept.py 后台线程
    ↓
循环检测游戏阶段 (lcu_api.get_gameflow_phase)
    ↓
检测到 "ReadyCheck" 阶段
    ↓
调用 lcu_api.accept_ready_check()
    ↓
向前端发送 'status_update' 消息
```

### 2. 敌我分析
```
用户点击"敌我分析"按钮
    ↓
前端 Socket.IO emit 'start_auto_analyze'
    ↓
websocket/socket_events.py 处理事件
    ↓
启动 services/auto_analyze.py 后台线程
    ↓
循环检测游戏阶段

阶段1: ChampSelect (选人)
    ↓
调用 lcu_api.get_champ_select_session()
    ↓
提取队友信息，记录 PUUID 到 config.app_state.current_teammates
    ↓
向前端发送 'teammates_found' 事件

阶段2: InProgress (游戏中)
    ↓
调用 lcu_api.get_all_players_from_game()
    ↓
从端口 2999 获取游戏数据 (allPlayers + activePlayer)
    ↓
根据 activePlayer 确定己方队伍 (ORDER/CHAOS)
    ↓
遍历 allPlayers，根据 team 字段分类：
    - team == my_team → 队友
    - team != my_team → 敌人
    ↓
双重过滤：排除 current_teammates 中的 PUUID（额外保险）
    ↓
向前端发送 'enemies_found' 事件
```

### 3. 战绩查询
```
用户输入召唤师名称，点击查询
    ↓
前端发送 GET /get_history?name=xxx
    ↓
routes/api_routes.py 处理请求
    ↓
调用 lcu_api.get_puuid() 获取 PUUID
    ↓
调用 lcu_api.get_match_history() 获取战绩
    ↓
处理数据，返回 JSON 响应
    ↓
前端展示战绩
```

## 模块依赖关系

```
app_new.py
    ├─> config.py (状态管理)
    ├─> routes/api_routes.py
    │       └─> config.py
    │       └─> lcu_api.py
    │       └─> constants.py
    ├─> websocket/socket_events.py
    │       └─> config.py
    │       └─> services/auto_accept.py
    │       └─> services/auto_analyze.py
    │       └─> lcu_api.py
    ├─> services/auto_accept.py
    │       └─> config.py
    │       └─> lcu_api.py
    ├─> services/auto_analyze.py
    │       └─> config.py
    │       └─> lcu_api.py
    └─> utils/network_utils.py
```

## 线程模型

```
主线程 (Flask App)
    │
    ├─> SocketIO 事件处理线程
    │
    ├─> 后台线程1: auto_accept_task
    │   (循环检测 ReadyCheck 阶段)
    │
    └─> 后台线程2: auto_analyze_task
        ├─> ChampSelect: 分析队友
        └─> InProgress: 分析敌人
```

## 状态管理

```
config.AppState (全局单例)
    │
    ├─> lcu_credentials
    │   ├─> auth_token
    │   └─> app_port
    │
    ├─> 功能开关
    │   ├─> auto_accept_enabled
    │   └─> auto_analyze_enabled
    │
    ├─> 分析状态
    │   ├─> teammate_analysis_done
    │   ├─> enemy_analysis_done
    │   └─> current_teammates (set)
    │
    └─> 线程引用
        ├─> auto_accept_thread
        └─> auto_analyze_thread
```
