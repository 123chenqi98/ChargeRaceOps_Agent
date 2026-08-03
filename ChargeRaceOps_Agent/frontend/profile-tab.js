const PROFILER_DATA = {
    dims: [
        {key: 'achievement', name: '目标达成', color: '#4facfe'},
        {key: 'momentum',    name: '增长动能', color: '#38ef7d'},
        {key: 'response',    name: '执行响应', color: '#a855f7'},
        {key: 'balance',     name: '团队均衡', color: '#fbbf24'},
        {key: 'stability',   name: '过程稳定', color: '#22d3ee'},
        {key: 'growth',      name: '成长潜力', color: '#f5576c'},
    ],
    bdms: [
        {
            name: '张伟', city: '绍兴一区', rank: 1, prevRank: 2,
            total: 75.1, grade: 'B', emoji: '👍', gradeLabel: 'B·稳步发展',
            seniority: 3.2, cmCount: 6,
            dims: {
                achievement: {score: 90.8, grade: 'S'},
                momentum:    {score: 63.7, grade: 'C'},
                response:    {score: 94.7, grade: 'S'},
                balance:     {score: 66.0, grade: 'C'},
                stability:   {score: 75.0, grade: 'B'},
                growth:      {score: 46.0, grade: 'D'},
            }
        },
        {
            name: '周婷', city: '宁波一区', rank: 2, prevRank: 4,
            total: 73.9, grade: 'B', emoji: '👍', gradeLabel: 'B·稳步发展',
            seniority: 2.0, cmCount: 4,
            dims: {
                achievement: {score: 82.7, grade: 'A'},
                momentum:    {score: 53.3, grade: 'D'},
                response:    {score: 87.2, grade: 'A'},
                balance:     {score: 72.0, grade: 'B'},
                stability:   {score: 70.0, grade: 'B'},
                growth:      {score: 55.0, grade: 'C'},
            }
        },
        {
            name: '黄磊', city: '温州一区', rank: 3, prevRank: 1,
            total: 69.3, grade: 'C', emoji: '⚡', gradeLabel: 'C·待加速',
            seniority: 2.8, cmCount: 5,
            dims: {
                achievement: {score: 72.3, grade: 'B'},
                momentum:    {score: 53.1, grade: 'D'},
                response:    {score: 91.5, grade: 'S'},
                balance:     {score: 62.0, grade: 'C'},
                stability:   {score: 68.0, grade: 'C'},
                growth:      {score: 62.0, grade: 'C'},
            }
        },
        {
            name: '朱超颖', city: '杭州一区', rank: 4, prevRank: 3,
            total: 68.9, grade: 'C', emoji: '⚡', gradeLabel: 'C·待加速',
            seniority: 2.1, cmCount: 5,
            dims: {
                achievement: {score: 77.3, grade: 'B'},
                momentum:    {score: 55.0, grade: 'D'},
                response:    {score: 89.5, grade: 'A'},
                balance:     {score: 60.0, grade: 'C'},
                stability:   {score: 68.0, grade: 'C'},
                growth:      {score: 58.0, grade: 'C'},
            }
        },
        {
            name: '陈静', city: '金华一区', rank: 5, prevRank: 5,
            total: 62.2, grade: 'C', emoji: '⚡', gradeLabel: 'C·待加速',
            seniority: 1.5, cmCount: 3,
            dims: {
                achievement: {score: 66.0, grade: 'C'},
                momentum:    {score: 54.0, grade: 'D'},
                response:    {score: 78.0, grade: 'B'},
                balance:     {score: 55.0, grade: 'D'},
                stability:   {score: 52.0, grade: 'D'},
                growth:      {score: 50.0, grade: 'D'},
            }
        },
        {
            name: '李明', city: '杭州二区', rank: 6, prevRank: 6,
            total: 49.7, grade: 'D', emoji: '🆘', gradeLabel: 'D·需帮扶',
            seniority: 1.0, cmCount: 4,
            dims: {
                achievement: {score: 50.0, grade: 'D'},
                momentum:    {score: 46.0, grade: 'D'},
                response:    {score: 62.0, grade: 'C'},
                balance:     {score: 50.0, grade: 'D'},
                stability:   {score: 48.0, grade: 'D'},
                growth:      {score: 42.0, grade: 'D'},
            }
        },
        {
            name: '刘强', city: '台州一区', rank: 7, prevRank: 8,
            total: 41.6, grade: 'D', emoji: '🆘', gradeLabel: 'D·需帮扶',
            seniority: 0.5, cmCount: 4,
            dims: {
                achievement: {score: 40.0, grade: 'D'},
                momentum:    {score: 38.0, grade: 'D'},
                response:    {score: 54.0, grade: 'D'},
                balance:     {score: 44.0, grade: 'D'},
                stability:   {score: 40.0, grade: 'D'},
                growth:      {score: 35.0, grade: 'D'},
            }
        },
        {
            name: '王鸿鹏', city: '杭州一区', rank: 8, prevRank: 7,
            total: 32.4, grade: 'D', emoji: '🆘', gradeLabel: 'D·需帮扶',
            seniority: 0.3, cmCount: 4,
            dims: {
                achievement: {score: 10.0, grade: 'D'},
                momentum:    {score: 25.0, grade: 'D'},
                response:    {score: 52.0, grade: 'D'},
                balance:     {score: 40.0, grade: 'D'},
                stability:   {score: 32.0, grade: 'D'},
                growth:      {score: 30.0, grade: 'D'},
            }
        }
    ]
};

let profileRadarChart;

function renderProfileTab() {
    renderRankList();
    renderProfileRadar();
}

function renderRankList() {
    const el = document.getElementById('profile-rank-list');
    if (!el) return;

    el.innerHTML = PROFILER_DATA.bdms.map(b => {
        const diff = (b.prevRank || b.rank) - b.rank;
        const trendHtml = diff > 0
            ? `<span class="rank-trend-up">▲${diff}</span>`
            : diff < 0
                ? `<span class="rank-trend-down">▼${-diff}</span>`
                : `<span class="rank-trend-flat">→</span>`;

        const gradeColor = {
            S: '#facc15', A: '#38ef7d', B: '#4facfe', C: '#ffa751', D: '#f5576c'
        }[b.grade] || '#888';

        const barHtml = PROFILER_DATA.dims.map(d => {
            const v = b.dims[d.key].score;
            return `<div class="bdm-bar"><div class="bdm-bar-fill" style="width:${v}%;background:${d.color}"></div></div>`;
        }).join('');
        const dimLabelHtml = PROFILER_DATA.dims.map(d => `<span title="${d.name}">${d.name.charAt(0)}</span>`).join('');

        return `
<div class="bdm-rank-item">
    <div>
        <div class="rank-badge ${b.rank <= 3 ? 'rank-' + b.rank : 'rank-other'}">${b.rank}</div>
        <div style="text-align:center;margin-top:4px;">${trendHtml}</div>
    </div>
    <div class="bdm-rank-meta">
        <div class="bdm-rank-title">
            <span class="bdm-name">${b.emoji} ${b.name}</span>
            <span class="bdm-city">${b.city}</span>
            <span class="bdm-grade-pill" style="color:${gradeColor};background:${gradeColor}22;">${b.gradeLabel}</span>
            <span class="bdm-city">资深${b.seniority}年</span>
            <span class="bdm-city">${b.cmCount}名CM</span>
        </div>
        <div class="bdm-bars">${barHtml}</div>
        <div class="bdm-dim-labels">${dimLabelHtml}</div>
    </div>
    <div class="bdm-score">
        <div class="bdm-score-num">${b.total}</div>
        <div class="bdm-score-label">综合得分</div>
    </div>
</div>`;
    }).join('');
}

function renderProfileRadar() {
    const el = document.getElementById('chart-profile-radar');
    if (!el) return;
    if (profileRadarChart) { profileRadarChart.dispose(); }
    profileRadarChart = echarts.init(el);

    const top4 = PROFILER_DATA.bdms.slice(0, 4);
    const indicators = PROFILER_DATA.dims.map(d => ({name: d.name, max: 100}));

    const colors = ['#4facfe', '#38ef7d', '#fbbf24', '#a855f7'];

    profileRadarChart.setOption({
        backgroundColor: 'transparent',
        tooltip: {
            backgroundColor: 'rgba(26,35,66,0.95)',
            borderColor: '#2a3560',
            textStyle: { color: '#e8ecf4', fontSize: 12 }
        },
        legend: {
            bottom: 0,
            textStyle: { color: '#8892b0', fontSize: 11 },
            itemWidth: 12, itemHeight: 8
        },
        radar: {
            indicator: indicators,
            center: ['50%', '48%'],
            radius: '60%',
            shape: 'polygon',
            splitNumber: 4,
            axisName: { color: '#8892b0', fontSize: 10 },
            splitArea: { areaStyle: { color: ['rgba(26,35,66,0.4)', 'rgba(18,26,53,0.4)'] } },
            axisLine: { lineStyle: { color: 'rgba(42,53,96,0.6)' } },
            splitLine: { lineStyle: { color: 'rgba(42,53,96,0.5)' } }
        },
        series: [{
            type: 'radar',
            data: top4.map((b, i) => ({
                name: `${b.name}(No.${b.rank})`,
                value: PROFILER_DATA.dims.map(d => b.dims[d.key].score),
                itemStyle: { color: colors[i] },
                areaStyle: { opacity: 0.15 },
                lineStyle: { width: 2 }
            }))
        }]
    });
}

function switchTab(name) {
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    event.target.closest('.nav-tab').classList.add('active');

    ['cockpit', 'profile', 'ai-report'].forEach(tabName => {
        const tab = document.getElementById('tab-' + tabName);
        if (tab) tab.classList.remove('active');
    });
    const active = document.getElementById('tab-' + name);
    if (active) {
        active.classList.add('active');
        if (name === 'profile') renderProfileTab();
        if (name === 'ai-report') renderAIReportTab();
        if (name === 'cockpit') {
            setTimeout(() => {
                [chartTrend, chartRulePie, chartBdmRank, chartForecast, chartHeatmap, chartRadar, chartSankey, chartGauge1, chartGauge2]
                    .forEach(c => c && c.resize());
            }, 50);
        }
    }

    setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
    }, 60);
}

function renderAIReportTab() {
    renderCausesSection();
    renderStrategySection();
    renderUrgeSection();
}

function renderCausesSection() {
    const el = document.getElementById('ai-cause-section');
    if (!el) return;
    const causes = [
        {name: '目标拆解未对齐（BDM-CM共识不足）', weight: '28%', probability: 0.92,
         action: '提前3天与每位CM面对面确认目标范围，每天10点确认缺口清单'},
        {name: 'POS/核销流程异常', weight: '25%', probability: 0.78,
         action: '联系商户运营申请备用核销码，门店店员留存APP下单入口'},
        {name: '重点门店支撑不足', weight: '20%', probability: 0.65,
         action: '下午起销售支持驻点TOP3未核销门店，协助现场核销'},
        {name: '周末激励政策未触达', weight: '15%', probability: 0.52,
         action: '一对一电话+群公告确认政策内容，2小时内回收CM确认回执'},
    ];
    el.innerHTML = causes.map(c => `
<div class="cause-item">
    <div class="cause-header">
        <span class="cause-name">${c.name}</span>
        <span class="cause-weight">权重 ${c.weight} · 置信度 ${Math.round(c.probability*100)}%</span>
    </div>
    <div class="cause-action">✅ 建议动作：${c.action}</div>
</div>`).join('');
}

function renderStrategySection() {
    const el = document.getElementById('ai-strategy-section');
    if (!el) return;
    const strategies = [
        {target: '🆘 王鸿鹏（D·需帮扶）',
         status: '当前综合10%，距离目标缺口最大',
         points: [
            '立刻联系杭州一区主管申请2名支援CM，和王鸿鹏的4名CM一一"结对陪跑"',
            '今天14点前，销售支持和王鸿鹏一起拉出TOP10未核销门店，逐个电话确认核销卡点',
            '对王鸿鹏启动"每日10分钟1v1复盘"，连续3天，直到他的完成度超过50%',
         ]},
        {target: '🆘 刘强（D·需帮扶）',
         status: '新人0.5年，CM培训不足是核心问题',
         points: [
            '从台州一区调配1名老CM，带教刘强团队中最弱的2名新人',
            '给他"降维目标"：先确保双计扫码核销达标，这个权重最低但信心最高',
            '周末前和刘强一起去3家重点门店现场"坐班"，用他的门店资源而非坐办公室'
         ]},
        {target: '⚡ 陈静（C·待加速）',
         status: '周末冲量乏力，连锁客户维护不够',
         points: [
            '本周六/日，陈静亲自带队跑TOP10连锁大客户，不要交给CM',
            '把金华一区的"新人激励金池"向陈静倾斜，重点激励周末核销TOP的CM',
            '向张伟、朱超颖要一份《大客户维护SOP》，让陈静在一周内学习并落地'
         ]},
    ];
    el.innerHTML = strategies.map(s => `
<div class="strategy-card">
    <div class="strategy-card-header">
        <div class="strategy-target">${s.target}</div>
        <span class="badge badge-red" style="background:rgba(245,87,108,0.15);color:#f5576c;">${s.status}</span>
    </div>
    <ul class="strategy-points">
        ${s.points.map(p => `<li>${p}</li>`).join('')}
    </ul>
</div>`).join('');
}

function renderUrgeSection() {
    const el = document.getElementById('ai-urge-section');
    if (!el) return;
    const samples = [
        {style: 'direct', label: '🎯 直接催办型', text:
`Hi 王鸿鹏，
当前双计核销完成度 **9.54%**，阈值 60%，R1 预警已触发。
请 **2小时内** ：
① 出TOP10未核销门店清单
② 与杭州一区主管确认支援方案
并点击预警卡片「已跟进」✅，我会在下次巡检复核。`
        },
        {style: 'encourage', label: '💪 鼓励打气型', text:
`Hi 陈静，你前面做得一直很稳！
距离双计目标还差 **38pct**，金华一区的CM们都在看你。
需要销售支持协助TOP门店冲刺，直接在群里@我，**24小时随时上**🔥
我们一起把数据打上去！加油 💪`
        },
        {style: 'detailed', label: '📌 归因+动作型', text:
`【预警·刘强·台州一区】
指标：双计核销 35% < 60%（R1触发）

🧠 归因TOP3：
① 新人培训不足（概率0.83）
② CM资源分配不均（概率0.76）
③ POS上周故障3次（概率0.58）

✅ 建议立即动作：
1. 下午14点前调1名老CM带教新人
2. 资源向台州TOP2门店重新倾斜
3. 申请备用核销码备用

需要协助随时拉群！销售支持A`
        }
    ];
    el.innerHTML = samples.map(s => `
<div class="urge-card">
    <span class="urge-card-header urge-style-${s.style}">${s.label}</span>
    <div class="urge-text">${s.text}</div>
</div>`).join('');
}

document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('tab-cockpit').classList.add('active');
});
