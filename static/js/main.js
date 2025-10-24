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
    
    // --- 辅助函数：跳转到召唤师详情页面 ---
    function navigateToSummonerDetail() {
        const summonerName = summonerNameInput.value.trim();
        if (!summonerName) {
            resultsDiv.innerHTML = '<p class="text-danger small"><i class="bi bi-exclamation-triangle me-1"></i>请输入召唤师名称 (格式: 名称#Tag)</p>';
            return;
        }
        
        // 直接跳转到召唤师详情页面
        const encodedName = encodeURIComponent(summonerName);
        window.location.href = `/summoner/${encodedName}`;
    }
    
    // --- 支持回车键快捷查询 ---
    summonerNameInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            navigateToSummonerDetail();
        }
    });
    
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
            
            // OP.GG integration removed: no external stats will be shown here.
            
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
        // 🚨 注意：后端我们有时使用 'message' 键，有时使用 'data' 键
        const message = data.message || data.data; // 兼容 'message' 和 'data' 键

        if (!statusElement || !statusBox) return;

        console.log('LCU状态更新:', message);

        // 只在后端发送与 LCU 连接相关的消息时更新 `#lcu-status`，
        // 避免把 "⚠️ 敌我分析功能已在运行中" 这样的业务状态覆盖连接状态导致逻辑误判。
        const isConnectionMessage = (
            (typeof message === 'string') && (
                message.includes('LCU') ||
                message.includes('本地服务器') ||
                message.includes('检测') ||
                message.includes('凭证') ||
                message.includes('端口') ||
                message.includes('连接成功') ||
                message.includes('连接 LCU') ||
                message.includes('LCU 连接') ||
                message.includes('连接 LCU 失败') ||
                message.includes('无法连接')
            )
        );

        if (isConnectionMessage) {
            // 仅更新显示 LCU 连接状态
            statusElement.textContent = message;

            // 根据连接相关关键词调整样式
            if (message.includes('成功') || message.includes('已获取')) {
                statusBox.style.backgroundColor = '#d4edda'; // 浅绿色
                statusBox.style.color = '#155724';
                statusBox.style.borderColor = '#c3e6cb';
            } else if (message.includes('失败') || message.includes('未运行') || message.includes('未找到') || message.includes('无法连接')) {
                statusBox.style.backgroundColor = '#f8d7da'; // 浅红色
                statusBox.style.color = '#721c24';
                statusBox.style.borderColor = '#f5c6cb';
            } else {
                statusBox.style.backgroundColor = '#cce5ff'; // 浅蓝色
                statusBox.style.color = '#004085';
                statusBox.style.borderColor = '#b8daff';
            }
        } else {
            // 非连接消息（如: 自动接受/敌我分析 的运行状态）显示在实时状态区域，且**不修改** LCU 连接显示
            realtimeStatus.textContent = message;
            // 简单设置样式：运行中的消息用警告色显示
            if (message.includes('运行中') || message.includes('已在运行')) {
                realtimeStatus.className = 'badge bg-warning text-dark';
            } else if (message.includes('开启') || message.includes('已开启') || message.includes('✅')) {
                realtimeStatus.className = 'badge bg-success';
            } else if (message.includes('无法') || message.includes('❌')) {
                realtimeStatus.className = 'badge bg-danger';
            } else {
                realtimeStatus.className = 'badge bg-secondary';
            }
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
        navigateToSummonerDetail();
    });
    
    function isLCUConnected() {
        const statusEl = document.getElementById('lcu-status');
        if (!statusEl) return false;
        const txt = (statusEl.textContent || '').toLowerCase();
        // consider connected if text mentions success or connected
        return txt.includes('成功') || txt.includes('已连接') || txt.includes('连接成功');
    }

    // --- Inline UI message helper (replaces alert) ---
    function showInlineMessage(message, level = 'warning', duration = 7000) {
        if (!realtimeStatus) return;
        // set class according to level
        let cls = 'badge ';
        if (level === 'success') cls += 'bg-success';
        else if (level === 'danger') cls += 'bg-danger';
        else if (level === 'info') cls += 'bg-info';
        else cls += 'bg-warning text-dark';

        realtimeStatus.textContent = message;
        realtimeStatus.className = cls;

        if (window._realtimeMessageTimer) {
            clearTimeout(window._realtimeMessageTimer);
        }
        if (duration > 0) {
            window._realtimeMessageTimer = setTimeout(() => {
                // clear message after duration
                realtimeStatus.textContent = '';
                realtimeStatus.className = '';
                window._realtimeMessageTimer = null;
            }, duration);
        }
    }

    autoAcceptBtn.addEventListener('click', () => {
        if (!isLCUConnected()) {
            showInlineMessage('无法启动自动接受：未检测到 LCU 连接。请先确保客户端已运行并允许本地 API 访问。', 'danger', 7000);
            return;
        }

        socket.emit('start_auto_accept');
        autoAcceptBtn.disabled = true;
        autoAcceptBtn.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> 运行中...';
        autoAcceptBtn.classList.remove('btn-success');
        autoAcceptBtn.classList.add('btn-secondary');
    });
    
    autoAnalyzeBtn.addEventListener('click', () => {
        if (!isLCUConnected()) {
            showInlineMessage('无法启动敌我分析：未检测到 LCU 连接。请先确保客户端已运行并允许本地 API 访问。', 'danger', 7000);
            return;
        }

        socket.emit('start_auto_analyze');
        autoAnalyzeBtn.disabled = true;
        autoAnalyzeBtn.innerHTML = '<i class="bi bi-bar-chart-fill me-1"></i> 运行中...';
        autoAnalyzeBtn.classList.remove('btn-primary');
        autoAnalyzeBtn.classList.add('btn-secondary');
    });
});
