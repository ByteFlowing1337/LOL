// api.js - functions that call server endpoints / helper for fetching summoner stats
import { qs } from './ui.js';

export async function fetchSummonerStats(gameName, tagLine, displayElement) {
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
                        <img src="https://ddragon.leagueoflegends.com/cdn/15.21.1/img/champion/${lastGame.champion_en}.png" 
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

export default { fetchSummonerStats };
