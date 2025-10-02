// static/js/main.js

document.addEventListener('DOMContentLoaded', () => {
    // --- WebSocket 初始化 ---
    const socket = io();

    // --- 获取HTML元素 ---
    const detectBtn = document.getElementById('detect-btn');
    const connectionStatus = document.getElementById('connection-status');
    const fetchBtn = document.getElementById('fetch-btn');
    const summonerNameInput = document.getElementById('summoner-name-input');
    const resultsDiv = document.getElementById('results-area');
    const autoAcceptBtn = document.getElementById('auto-accept-btn');
    const autoAnalyzeBtn = document.getElementById('auto-analyze-btn');
    const realtimeStatus = document.getElementById('realtime-status');
    const teammateResultsDiv = document.getElementById('teammate-results-area');
    const enemyResultsDiv = document.getElementById('enemy-results-area'); 
    
    // --- 辅助函数: 异步获取单个召唤师的战绩 ---
async function fetchSummonerStats(gameName, tagLine, displayElement) {
    const apiEndpoint = '/get_history'; 
    const fullRiotId = `${gameName}#${tagLine}`;
    const encodedRiotId = encodeURIComponent(fullRiotId);

    try {
        const response = await fetch(`${apiEndpoint}?name=${encodedRiotId}`); 

        if (!response.ok) {
            throw new Error(`HTTP 错误! 状态码: ${response.status}`);
        }

        const data = await response.json();

        if (data.success && data.games && data.games.length > 0) {
            const games = data.games;
            const totalGames = games.length;
            const wins = games.filter(game => game.win).length;
            const losses = totalGames - wins;
            const winRate = ((wins / totalGames) * 100).toFixed(1);
            
            // 计算KDA平均值
            let totalKills = 0, totalDeaths = 0, totalAssists = 0;
            games.forEach(game => {
                const kdaParts = game.kda.split('/');
                totalKills += parseInt(kdaParts[0]) || 0;
                totalDeaths += parseInt(kdaParts[1]) || 0;
                totalAssists += parseInt(kdaParts[2]) || 0;
            });
            const avgKDA = totalDeaths > 0 ? ((totalKills + totalAssists) / totalDeaths).toFixed(2) : 'Perfect';
            
            // 提取最近一场数据
            const lastGame = games[0];
            const resultText = lastGame.win ? '胜' : '败';
            const resultClass = lastGame.win ? 'text-success fw-bold' : 'text-danger fw-bold';
            const winRateClass = winRate >= 60 ? 'text-success' : winRate >= 50 ? 'text-warning' : 'text-danger';
            
            // OP.GG数据
            let opggInfo = '';
            if (lastGame.opgg) {
                const tier = lastGame.opgg.tier || 'N/A';
                const champWinRate = lastGame.opgg.win_rate ? lastGame.opgg.win_rate.toFixed(1) + '%' : 'N/A';
                const tierColor = tier === 'S' ? 'success' : tier === 'A' ? 'info' : tier === 'B' ? 'warning' : 'secondary';
                opggInfo = `
                    <div class="mt-1">
                        <span class="badge bg-${tierColor}" style="font-size: 0.75em;" title="OP.GG Tier评级">Tier ${tier}</span>
                        <span class="badge bg-primary" style="font-size: 0.75em;" title="该英雄当前版本胜率">胜率 ${champWinRate}</span>
                    </div>
                `;
            }
            
            displayElement.innerHTML = `
                <div class="small mt-1">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="badge bg-secondary">最近${totalGames}场</span>
                        <span class="${winRateClass} fw-bold">${wins}胜${losses}败 (${winRate}%)</span>
                    </div>
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="text-muted">平均KDA: <strong class="text-info">${avgKDA}</strong></span>
                        <span class="${resultClass}">上局: ${resultText}</span>
                    </div>
                    <div class="text-muted" style="font-size: 0.85em;">
                        <img src="https://ddragon.leagueoflegends.com/cdn/14.13.1/img/champion/${lastGame.champion_en}.png" 
                             alt="${lastGame.champion_en}" 
                             width="20" 
                             height="20"
                             style="vertical-align: middle; border-radius: 3px;">
                        ${lastGame.champion_en} | ${lastGame.kda}
                        ${opggInfo}
                    </div>
                </div>
            `;
            
        } else if (data.success) {
            displayElement.innerHTML = `<div class="small text-warning mt-1">📊 无战绩数据</div>`;
        } else {
            displayElement.innerHTML = `<div class="small text-danger mt-1">❌ ${data.message || '查询失败'}</div>`;
        }

    } catch (error) {
        console.error(`获取 ${fullRiotId} 战绩失败:`, error);
        displayElement.innerHTML = `<div class="small text-danger mt-1">❌ 查询失败</div>`;
    }
}
    // --- WebSocket 事件监听 ---
    socket.on('enemies_found', async (data) => {
        console.log('发现敌人:', data.enemies);
        realtimeStatus.textContent = `💥 发现 ${data.enemies.length} 名敌人! 正在分析战绩...`;
        realtimeStatus.className = 'badge bg-danger'; // 红色标识敌人
        
        // 清空并设置标题
        enemyResultsDiv.innerHTML = '<h5 class="text-danger"><i class="bi bi-exclamation-triangle-fill me-2"></i>敌方目标分析:</h5>';
        const ul = document.createElement('ul');
        ul.className = 'list-unstyled';
        enemyResultsDiv.appendChild(ul);

        // 使用 Promise.all 并行处理所有敌人
        const promises = data.enemies.map(enemy => {
            const li = document.createElement('li');
            li.className = 'd-flex flex-column border-bottom py-2 mb-2';
            
            // 1. 显示 Riot ID 和英雄（可点击跳转）
            const headerDiv = document.createElement('div');
            headerDiv.className = 'd-flex justify-content-between align-items-center';
            
            const riotIdLink = document.createElement('a');
            riotIdLink.href = `/summoner/${encodeURIComponent(enemy.gameName + '#' + enemy.tagLine)}`;
            riotIdLink.className = 'fw-bold text-danger text-decoration-none';
            riotIdLink.style.cursor = 'pointer';
            riotIdLink.innerHTML = `<i class="bi bi-person-x-fill me-1"></i>${enemy.gameName}#${enemy.tagLine}`;
            riotIdLink.title = '点击查看详细战绩';
            headerDiv.appendChild(riotIdLink);
            
            // 显示英雄信息（如果有）
            if (enemy.championId && enemy.championId !== 'Unknown') {
                const championSpan = document.createElement('span');
                championSpan.className = 'badge bg-dark';
                championSpan.textContent = enemy.championId;
                headerDiv.appendChild(championSpan);
            }
            
            li.appendChild(headerDiv);

            // 2. 战绩显示区域（占位符/加载状态）
            const statsDisplay = document.createElement('div');
            statsDisplay.textContent = '⏳ 查询中...';
            statsDisplay.className = 'text-muted small mt-1';
            li.appendChild(statsDisplay);
            
            ul.appendChild(li);

            // 3. 异步调用战绩查询函数
            return fetchSummonerStats(enemy.gameName, enemy.tagLine, statsDisplay);
        });

        // 等待所有查询完成
        await Promise.all(promises);

        realtimeStatus.textContent = `✅ 敌方战绩分析完成!`;
        realtimeStatus.className = 'badge bg-success';
    });
    socket.on('connect', () => {
        console.log('成功连接到WebSocket服务器!');
    });

    // 🎯 1. 监听后端发送的 'status_update' 事件
     socket.on('connect', () => {
        console.log('成功连接到WebSocket服务器!');
    });

    socket.on('status_update', function(data) {
        const statusElement = document.getElementById('lcu-status');
        const statusBox = document.getElementById('connection-status-box');
        // 🚨 注意：后端 app.py 中，我们使用 'message' 键发送消息
        const message = data.message || data.data; // 兼容 'message' 和 'data' 键

        if (!statusElement || !statusBox) return;

        console.log('LCU状态更新:', message);
        statusElement.textContent = message; // 🎯 仅更新 LCU 连接状态框

        // 🎯 移除：不再让 LCU 连接状态更新 `#realtime-status` 区域。
        // `#realtime-status` 将只在 'start_auto_accept' 按钮点击时更新。

        // 2. 根据消息内容判断状态并设置样式
        if (message.includes('成功')) {
            // 连接成功 (绿色背景)
            statusBox.style.backgroundColor = '#d4edda'; // 浅绿色
            statusBox.style.color = '#155724'; // 深绿色文本
            statusBox.style.borderColor = '#c3e6cb'; // 边框
        } else if (message.includes('失败') || message.includes('未运行') || message.includes('未找到')) {
            // 连接失败 (红色背景)
            statusBox.style.backgroundColor = '#f8d7da'; // 浅红色
            statusBox.style.color = '#721c24'; // 深红色文本
            statusBox.style.borderColor = '#f5c6cb'; // 边框
        } else {
            // 正在检测中/等待指令 (蓝色/中性背景)
            statusBox.style.backgroundColor = '#cce5ff'; // 浅蓝色
            statusBox.style.color = '#004085'; // 深蓝色文本
            statusBox.style.borderColor = '#b8daff'; // 边框
        }
    });

    socket.on('teammates_found', async (data) => {
        console.log('发现队友:', data.teammates);
        realtimeStatus.textContent = `👥 发现 ${data.teammates.length} 名队友! 正在分析战绩...`;
        realtimeStatus.className = 'badge bg-info';
        
        // 清空并设置标题
        teammateResultsDiv.innerHTML = '<h5 class="text-primary"><i class="bi bi-people-fill me-2"></i>本局队友分析:</h5>';
        const ul = document.createElement('ul');
        ul.className = 'list-unstyled';
        teammateResultsDiv.appendChild(ul);

        // 使用 Promise.all 并行处理所有队友，加快查询速度
        const promises = data.teammates.map(tm => {
            const li = document.createElement('li');
            li.className = 'd-flex flex-column border-bottom py-2 mb-2';
            
            // 1. 显示 Riot ID（可点击跳转）
            const headerDiv = document.createElement('div');
            headerDiv.className = 'd-flex justify-content-between align-items-center';
            
            const riotIdLink = document.createElement('a');
            riotIdLink.href = `/summoner/${encodeURIComponent(tm.gameName + '#' + tm.tagLine)}`;
            riotIdLink.className = 'fw-bold text-primary text-decoration-none';
            riotIdLink.style.cursor = 'pointer';
            riotIdLink.innerHTML = `<i class="bi bi-person-check-fill me-1"></i>${tm.gameName}#${tm.tagLine}`;
            riotIdLink.title = '点击查看详细战绩';
            headerDiv.appendChild(riotIdLink);
            
            li.appendChild(headerDiv);

            // 2. 战绩显示区域（占位符/加载状态）
            const statsDisplay = document.createElement('div');
            statsDisplay.textContent = '⏳ 查询中...';
            statsDisplay.className = 'text-muted small mt-1';
            li.appendChild(statsDisplay);
            
            ul.appendChild(li);

            // 3. 异步调用战绩查询函数
            return fetchSummonerStats(tm.gameName, tm.tagLine, statsDisplay);
        });

        // 等待所有查询完成 (界面会先显示 '查询中...')
        await Promise.all(promises);

        realtimeStatus.textContent = `✅ 队友分析完成! 等待游戏开始...`;
        realtimeStatus.className = 'badge bg-success';
        console.log('队友战绩分析全部完成');
    });

    // --- 按钮点击事件 ---
   


    fetchBtn.addEventListener('click', () => {
        const summonerName = summonerNameInput.value.trim();
        if (!summonerName) {
            // LCU Canvas 环境中禁用 alert()，使用更友好的方式显示错误
            resultsDiv.textContent = '请输入召唤师名称 (格式: 名称#Tag)';
            resultsDiv.style.color = 'red';
            return;
        }
        resultsDiv.innerHTML = '正在查询...';
        resultsDiv.style.color = 'black'; // Reset color

        // 核心修复：将名称 URL 编码后，作为查询参数 'name' 传递
        const encodedName = encodeURIComponent(summonerName);
        const fetchUrl = `/get_history?name=${encodedName}`;

        fetch(fetchUrl) 
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    let html = '<h3>最近战绩:</h3>';
                    data.games.forEach(game => {
                        const resultClass = game.win ? 'win-text' : 'loss-text'; // 假设 CSS 中有这两个类
                        const resultText = game.win ? '胜利' : '失败';
                        // 使用 DDragon 最新版本路径
                        html += `
                            <p class="game-item ${resultClass}">
                                <img src="https://ddragon.leagueoflegends.com/cdn/14.13.1/img/champion/${game.champion_en}.png" 
                                     alt="${game.champion_en}" width="32" style="vertical-align: middle; border-radius: 50%;">
                                <strong>${game.champion_en}</strong> | 
                                KDA: ${game.kda} | 
                                <span class="${resultClass} font-bold">${resultText}</span> (${game.gameMode})
                            </p>
                        `;
                    });
                    resultsDiv.innerHTML = html;
                } else {
                    resultsDiv.textContent = `查询失败: ${data.message}`;
                    resultsDiv.style.color = 'red';
                }
            })
            .catch(error => {
                resultsDiv.textContent = `请求失败: 服务器连接错误或JSON解析失败。`;
                resultsDiv.style.color = 'red';
                console.error("Fetch Error:", error);
            });
    });
    
    autoAcceptBtn.addEventListener('click', () => {
        socket.emit('start_auto_accept');
        autoAcceptBtn.disabled = true;
        autoAcceptBtn.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> 运行中...';
        autoAcceptBtn.classList.remove('btn-success');
        autoAcceptBtn.classList.add('btn-secondary');
    });
    
    autoAnalyzeBtn.addEventListener('click', () => {
        socket.emit('start_auto_analyze');
        autoAnalyzeBtn.disabled = true;
        autoAnalyzeBtn.innerHTML = '<i class="bi bi-bar-chart-fill me-1"></i> 运行中...';
        autoAnalyzeBtn.classList.remove('btn-primary');
        autoAnalyzeBtn.classList.add('btn-secondary');
    });
});
