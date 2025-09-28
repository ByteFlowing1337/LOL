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
    const realtimeStatus = document.getElementById('realtime-status');
    const teammateResultsDiv = document.getElementById('teammate-results-area');

    // --- WebSocket 事件监听 ---
    socket.on('connect', () => {
        console.log('成功连接到WebSocket服务器!');
    });

    socket.on('status_update', (data) => {
        console.log('状态更新:', data.message);
        realtimeStatus.textContent = data.message;
    });

    socket.on('teammates_found', (data) => {
        console.log('发现队友:', data.teammates);
        realtimeStatus.textContent = `发现 ${data.teammates.length} 名队友!`;
        teammateResultsDiv.innerHTML = '<h3>本局队友:</h3>';
        const ul = document.createElement('ul');
        data.teammates.forEach(tm => {
            const li = document.createElement('li');
            // Riot ID (GameName#TagLine)
            li.textContent = `${tm.gameName}#${tm.tagLine}`;
            ul.appendChild(li);
        });
        teammateResultsDiv.appendChild(ul);
        // 这里可以进一步为每个队友调用获取战绩的API
    });

    // --- 按钮点击事件 ---
    detectBtn.addEventListener('click', () => {
        connectionStatus.textContent = '正在检测 LCU 客户端...';
        connectionStatus.style.color = '#f97316'; // Orange color while detecting

        fetch('/autodetect', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    connectionStatus.textContent = `✅ 已连接 (端口: ${data.port})`;
                    connectionStatus.style.color = 'green';
                } else {
                    connectionStatus.textContent = `❌ 检测失败: ${data.message}`;
                    connectionStatus.style.color = 'red';
                }
            })
            .catch(() => {
                connectionStatus.textContent = '❌ 连接服务器失败，请检查后端运行状态。';
                connectionStatus.style.color = 'red';
            });
    });

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
                                     alt="${game.champion_zh}" width="32" style="vertical-align: middle; border-radius: 50%;">
                                <strong>${game.champion_zh}</strong> | 
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
        realtimeStatus.textContent = '已发送开启指令，等待游戏事件...';
    });
});
