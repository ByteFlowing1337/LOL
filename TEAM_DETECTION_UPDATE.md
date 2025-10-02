# 敌我识别逻辑更新说明

## 修改日期
2025-10-02

## 修改原因
之前的逻辑假设 `allPlayers` 数组中前5人是队友，后5人是敌人，但这个假设不够可靠。
实际上，游戏API在 `allPlayers` 中为每个玩家提供了 `team` 字段，值为 "ORDER" 或 "CHAOS"。

## 旧逻辑（基于索引）
```python
# 前5人 (索引 0-4) → 队友
if i < 5:
    teammate_list.append(player_info)

# 后5人 (索引 5-9) → 敌人
else:
    enemy_list.append(player_info)
```

**问题：**
- ❌ 依赖数组顺序，不够健壮
- ❌ 如果API返回顺序改变，逻辑会失效
- ❌ 没有使用官方提供的 `team` 字段

## 新逻辑（基于队伍字段）

### 工作流程
```python
1. 获取游戏数据 (get_live_game_data)
   ↓
2. 从 activePlayer 获取当前玩家的召唤师名
   ↓
3. 在 allPlayers 中查找该玩家，获取其 team 字段
   ↓
4. 遍历所有玩家：
   - 如果 player.team == my_team → 队友
   - 如果 player.team != my_team → 敌人
```

### 代码示例
```python
# 获取当前玩家的队伍
active_player = game_data.get('activePlayer', {})
my_team = active_player.get('summonerName', '')

# 找到当前玩家在 allPlayers 中的 team
for player in all_players:
    if player.get('summonerName') == my_team:
        my_team_side = player.get('team', '')  # "ORDER" 或 "CHAOS"
        break

# 根据 team 字段分类
for player in all_players:
    player_team = player.get('team', '')
    
    if player_team == my_team_side:
        # 队友（同队伍）
        teammate_list.append(player_info)
    else:
        # 敌人（不同队伍）
        enemy_list.append(player_info)
```

## API 数据结构示例

### activePlayer
```json
{
  "summonerName": "Player1#TAG1",
  "championName": "Ahri",
  ...
}
```

### allPlayers (片段)
```json
{
  "allPlayers": [
    {
      "summonerName": "Player1#TAG1",
      "team": "ORDER",
      "championName": "Ahri",
      ...
    },
    {
      "summonerName": "Player2#TAG2",
      "team": "ORDER",
      "championName": "Yasuo",
      ...
    },
    ...
    {
      "summonerName": "Enemy1#TAG1",
      "team": "CHAOS",
      "championName": "Zed",
      ...
    },
    ...
  ]
}
```

## 优势对比

| 特性 | 旧逻辑（索引） | 新逻辑（team字段） |
|------|---------------|-------------------|
| **可靠性** | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **准确性** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **健壮性** | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **官方支持** | ❌ | ✅ |
| **未来兼容** | ⭐⭐ | ⭐⭐⭐⭐⭐ |

## 额外保护机制

新逻辑仍然保留了 PUUID 过滤机制作为双重保险：

```python
# 在 ChampSelect 阶段记录队友 PUUID
app_state.current_teammates.add(puuid)

# 在 InProgress 阶段进行双重过滤
if app_state.current_teammates:
    for enemy in enemies:
        if enemy['puuid'] not in app_state.current_teammates:
            filtered_enemies.append(enemy)
```

这样即使 `team` 字段出现异常，也有备用机制保证准确性。

## 日志输出示例

### 成功识别
```
🎮 当前玩家队伍: ORDER
👥 队友: Player1#TAG1 (Ahri) [队伍: ORDER]
👥 队友: Player2#TAG2 (Yasuo) [队伍: ORDER]
👥 队友: Player3#TAG3 (Lee Sin) [队伍: ORDER]
👥 队友: Player4#TAG4 (Thresh) [队伍: ORDER]
👥 队友: Player5#TAG5 (Jinx) [队伍: ORDER]
💥 敌人: Enemy1#TAG1 (Zed) [队伍: CHAOS]
💥 敌人: Enemy2#TAG2 (Malphite) [队伍: CHAOS]
💥 敌人: Enemy3#TAG3 (Lux) [队伍: CHAOS]
💥 敌人: Enemy4#TAG4 (Blitzcrank) [队伍: CHAOS]
💥 敌人: Enemy5#TAG5 (Caitlyn) [队伍: CHAOS]
✅ 成功获取 5 名队友 (ORDER) 和 5 名敌人
```

## 测试建议

1. ✅ 启动一局游戏
2. ✅ 点击"敌我分析"按钮
3. ✅ 检查控制台日志，确认队伍识别正确
4. ✅ 验证前端显示的队友和敌人列表
5. ✅ 对比游戏内实际队伍，确保100%准确

## 影响的文件

1. `lcu_api.py` - 修改 `get_all_players_from_game()` 函数
2. `services/auto_analyze.py` - 更新注释
3. `ARCHITECTURE.md` - 更新架构文档

## 向后兼容性

✅ 完全兼容，不影响其他功能：
- ChampSelect 阶段队友分析 - 不受影响
- PUUID 过滤机制 - 保留作为双重保险
- 前端显示 - 无需修改
- WebSocket 事件 - 无需修改

## 总结

这次修改使用了游戏API官方提供的 `team` 字段来区分敌我，比基于数组索引的假设更加可靠和准确。
同时保留了 PUUID 过滤机制作为额外保护，确保在任何情况下都能正确识别敌我双方。
