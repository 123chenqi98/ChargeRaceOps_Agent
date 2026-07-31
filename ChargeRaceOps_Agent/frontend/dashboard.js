let chartTrend, chartRulePie, chartBdmRank, chartForecast, chartHeatmap, chartRadar, chartSankey, chartGauge1, chartGauge2;
let currentBdmFilter = 'single';
let currentAlertFilter = 'all';

document.addEventListener('DOMContentLoaded', function () {
    updateTime();
    setInterval(updateTime, 1000);
    initCharts();
    renderAlertTable();
    window.addEventListener('resize', function () {
        [chartTrend, chartRulePie, chartBdmRank, chartForecast, chartHeatmap, chartRadar, chartSankey, chartGauge1, chartGauge2]
            .forEach(c => c && c.resize());
    });
});

function updateTime() {
    const now = new Date();
    const str = now.toLocaleString('zh-CN', {
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit', second: '2-digit',
        hour12: false
    }).replace(/\//g, '-');
    document.getElementById('current-time').textContent = str;
}

function initCharts() {
    chartTrend = echarts.init(document.getElementById('chart-trend'));
    chartRulePie = echarts.init(document.getElementById('chart-rule-pie'));
    chartBdmRank = echarts.init(document.getElementById('chart-bdm-rank'));
    chartForecast = echarts.init(document.getElementById('chart-forecast'));
    chartHeatmap = echarts.init(document.getElementById('chart-heatmap'));
    chartRadar = echarts.init(document.getElementById('chart-radar'));
    chartSankey = echarts.init(document.getElementById('chart-sankey'));
    chartGauge1 = echarts.init(document.getElementById('chart-gauge1'));
    chartGauge2 = echarts.init(document.getElementById('chart-gauge2'));

    renderTrendChart();
    renderRulePie();
    renderBdmRank(currentBdmFilter);
    renderForecastChart();
    renderHeatmap();
    renderRadar();
    renderSankey();
    renderGauges();
}

function renderTrendChart() {
    const d = genTrendData();
    const option = {
        backgroundColor: 'transparent',
        grid: { top: 30, right: 20, bottom: 40, left: 50 },
        legend: { show: false, data: ['R1', 'R2', 'R3', 'R4'] },
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(26,35,66,0.95)',
            borderColor: '#2a3560',
            textStyle: { color: '#e8ecf4', fontSize: 12 },
            axisPointer: { type: 'cross', label: { backgroundColor: '#4facfe' } }
        },
        xAxis: {
            type: 'category',
            data: d.times,
            axisLine: { lineStyle: { color: '#2a3560' } },
            axisLabel: { color: '#8892b0', fontSize: 10, interval: 8 },
            splitLine: { show: false }
        },
        yAxis: {
            type: 'value',
            name: '预警数',
            nameTextStyle: { color: '#8892b0', fontSize: 10 },
            axisLine: { show: false },
            axisLabel: { color: '#8892b0', fontSize: 10 },
            splitLine: { lineStyle: { color: 'rgba(42,53,96,0.4)', type: 'dashed' } }
        },
        series: [
            { name: 'R1低完成率', type: 'line', smooth: true, symbol: 'none',
              lineStyle: { color: '#4facfe', width: 2.5 },
              areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: 'rgba(79,172,254,0.35)' }, { offset: 1, color: 'rgba(79,172,254,0)' }
              ]) },
              data: d.R1 },
            { name: 'R2增速停滞', type: 'line', smooth: true, symbol: 'none',
              lineStyle: { color: '#ffa751', width: 2.5 },
              areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: 'rgba(255,167,81,0.3)' }, { offset: 1, color: 'rgba(255,167,81,0)' }
              ]) },
              data: d.R2 },
            { name: 'R3冲刺不足', type: 'line', smooth: true, symbol: 'none',
              lineStyle: { color: '#38ef7d', width: 2 },
              areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: 'rgba(56,239,125,0.25)' }, { offset: 1, color: 'rgba(56,239,125,0)' }
              ]) },
              data: d.R3 },
            { name: 'R4层级失衡', type: 'line', smooth: true, symbol: 'none',
              lineStyle: { color: '#a855f7', width: 2 },
              areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: 'rgba(168,85,247,0.25)' }, { offset: 1, color: 'rgba(168,85,247,0)' }
              ]) },
              data: d.R4 }
        ]
    };
    chartTrend.setOption(option);
}

function renderRulePie() {
    const d = genRuleDist();
    const total = d.reduce((s, x) => s + x.value, 0);
    const option = {
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'item',
            backgroundColor: 'rgba(26,35,66,0.95)',
            borderColor: '#2a3560',
            textStyle: { color: '#e8ecf4', fontSize: 12 },
            formatter: '{b}<br/>数量：{c}<br/>占比：{d}%'
        },
        legend: {
            bottom: 0, left: 'center',
            textStyle: { color: '#8892b0', fontSize: 10 },
            itemWidth: 10, itemHeight: 10
        },
        title: {
            text: total + '条',
            subtext: '累计预警',
            left: 'center', top: '38%',
            textStyle: { color: '#e8ecf4', fontSize: 24, fontWeight: 700 },
            subtextStyle: { color: '#8892b0', fontSize: 11 }
        },
        series: [{
            type: 'pie',
            radius: ['48%', '72%'],
            center: ['50%', '45%'],
            avoidLabelOverlap: true,
            itemStyle: { borderWidth: 3, borderColor: '#1a2342', borderRadius: 4 },
            label: { show: true, formatter: '{d}%', color: '#8892b0', fontSize: 11 },
            labelLine: { length: 8, length2: 6, lineStyle: { color: '#2a3560' } },
            data: d
        }]
    };
    chartRulePie.setOption(option);
}

function renderBdmRank(type) {
    const d = genBdmRankData(type);
    const labelMap = { single: '单计核销完成度(%)', double: '双计核销完成度(%)', scan: '双计扫码完成度(%)', comprehensive: '综合达成(%)' };
    const colors = d.values.map(v =>
        v < 40 ? '#f5576c' : v < 60 ? '#ffa751' : v < 80 ? '#fbbf24' : '#38ef7d'
    );

    const option = {
        backgroundColor: 'transparent',
        grid: { top: 10, right: 40, bottom: 20, left: 90 },
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' },
            backgroundColor: 'rgba(26,35,66,0.95)',
            borderColor: '#2a3560',
            textStyle: { color: '#e8ecf4', fontSize: 12 },
            formatter: params => {
                const p = params[0];
                return `${p.name}<br/>${labelMap[type]}：<b>${p.value}</b>`;
            }
        },
        xAxis: {
            type: 'value', max: 100,
            axisLine: { lineStyle: { color: '#2a3560' } },
            axisLabel: { color: '#8892b0', fontSize: 10, formatter: '{value}%' },
            splitLine: { lineStyle: { color: 'rgba(42,53,96,0.4)', type: 'dashed' } }
        },
        yAxis: {
            type: 'category',
            data: d.names,
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: { color: '#e8ecf4', fontSize: 12 }
        },
        series: [{
            type: 'bar',
            data: d.values.map((v, i) => ({ value: v, itemStyle: { color: colors[i], borderRadius: [0, 4, 4, 0] } })),
            barWidth: 16,
            label: {
                show: true, position: 'right',
                color: '#e8ecf4', fontSize: 11,
                formatter: '{c}%'
            },
            markLine: {
                silent: true, symbol: 'none',
                lineStyle: { color: '#fbbf24', type: 'dashed', width: 2 },
                data: [{ xAxis: 60, label: { color: '#fbbf24', fontSize: 10, formatter: '目标线 60%', position: 'insideEndTop' } }]
            }
        }]
    };
    chartBdmRank.setOption(option);
}

function filterBdmRank(type) {
    currentBdmFilter = type;
    document.querySelectorAll('.filter-tabs .tab-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    renderBdmRank(type);
}

function renderForecastChart() {
    const d = genForecastData();
    const option = {
        backgroundColor: 'transparent',
        grid: { top: 40, right: 20, bottom: 35, left: 50 },
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(26,35,66,0.95)',
            borderColor: '#2a3560',
            textStyle: { color: '#e8ecf4', fontSize: 12 }
        },
        legend: {
            top: 0, right: 10,
            textStyle: { color: '#8892b0', fontSize: 10 },
            itemWidth: 14, itemHeight: 8
        },
        xAxis: {
            type: 'category',
            data: d.times,
            axisLine: { lineStyle: { color: '#2a3560' } },
            axisLabel: { color: '#8892b0', fontSize: 10 }
        },
        yAxis: {
            type: 'value', max: 110,
            axisLine: { show: false },
            axisLabel: { color: '#8892b0', fontSize: 10, formatter: '{value}%' },
            splitLine: { lineStyle: { color: 'rgba(42,53,96,0.4)', type: 'dashed' } }
        },
        series: [
            { name: '实际达成', type: 'line', smooth: true, symbol: 'circle', symbolSize: 6,
              itemStyle: { color: '#4facfe' },
              lineStyle: { color: '#4facfe', width: 3 },
              areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: 'rgba(79,172,254,0.4)' }, { offset: 1, color: 'rgba(79,172,254,0.05)' }
              ]) },
              data: d.actual
            },
            { name: '预测达成', type: 'line', smooth: true, symbol: 'none',
              itemStyle: { color: '#38ef7d' },
              lineStyle: { color: '#38ef7d', width: 2, type: 'dashed' },
              data: d.predicted
            },
            { name: '目标线', type: 'line',
              lineStyle: { color: '#f5576c', type: 'dashed', width: 2 },
              itemStyle: { color: '#f5576c' },
              symbol: 'none',
              markLine: {
                  silent: true, symbol: 'none',
                  lineStyle: { color: '#f5576c', type: 'dashed', width: 2 },
                  data: [{ yAxis: d.target, label: { color: '#f5576c', fontSize: 10, formatter: '目标100%', position: 'insideEndTop' } }]
              },
              data: d.times.map(() => null)
            }
        ]
    };
    chartForecast.setOption(option);
}

function renderHeatmap() {
    const d = genHeatmapData();
    const option = {
        backgroundColor: 'transparent',
        tooltip: {
            position: 'top',
            backgroundColor: 'rgba(26,35,66,0.95)',
            borderColor: '#2a3560',
            textStyle: { color: '#e8ecf4', fontSize: 12 },
            formatter: p => `${d.yLabels[p.value[1]]} / ${d.xLabels[p.value[0]]}<br/>综合达成：<b>${p.value[2]}</b>`
        },
        grid: { top: 20, right: 35, bottom: 45, left: 65 },
        xAxis: {
            type: 'category',
            data: d.xLabels,
            splitArea: { show: true, areaStyle: { color: ['rgba(26,35,66,0.3)', 'transparent'] } },
            axisLine: { lineStyle: { color: '#2a3560' } },
            axisLabel: { color: '#8892b0', fontSize: 10 }
        },
        yAxis: {
            type: 'category',
            data: d.yLabels,
            splitArea: { show: true },
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: { color: '#e8ecf4', fontSize: 10 }
        },
        visualMap: {
            min: 0, max: 100,
            calculable: true,
            orient: 'horizontal',
            left: 'center',
            bottom: 0,
            itemHeight: 10,
            itemWidth: 120,
            textStyle: { color: '#8892b0', fontSize: 10 },
            inRange: { color: ['#f5576c', '#ffa751', '#fbbf24', '#38ef7d', '#11998e'] }
        },
        series: [{
            name: '综合达成',
            type: 'heatmap',
            data: d.data,
            label: {
                show: true,
                color: '#fff',
                fontSize: 10,
                formatter: p => p.value[2]
            },
            itemStyle: {
                borderColor: '#1a2342',
                borderWidth: 2
            },
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        }]
    };
    chartHeatmap.setOption(option);
}

function renderRadar() {
    const d = genRadarData();
    const option = {
        backgroundColor: 'transparent',
        tooltip: {
            backgroundColor: 'rgba(26,35,66,0.95)',
            borderColor: '#2a3560',
            textStyle: { color: '#e8ecf4', fontSize: 11 }
        },
        legend: {
            bottom: 0,
            textStyle: { color: '#8892b0', fontSize: 10 },
            itemWidth: 10, itemHeight: 10
        },
        radar: {
            indicator: d.indicators,
            shape: 'polygon',
            center: ['50%', '48%'],
            radius: '60%',
            splitNumber: 4,
            axisName: { color: '#8892b0', fontSize: 10 },
            splitArea: { areaStyle: { color: ['rgba(26,35,66,0.3)', 'rgba(18,26,53,0.3)'] } },
            axisLine: { lineStyle: { color: 'rgba(42,53,96,0.6)' } },
            splitLine: { lineStyle: { color: 'rgba(42,53,96,0.5)' } }
        },
        series: [{
            type: 'radar',
            data: d.series
        }]
    };
    chartRadar.setOption(option);
}

function renderSankey() {
    const d = genSankeyData();
    const option = {
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'item',
            backgroundColor: 'rgba(26,35,66,0.95)',
            borderColor: '#2a3560',
            textStyle: { color: '#e8ecf4', fontSize: 11 }
        },
        series: [{
            type: 'sankey',
            layout: 'none',
            emphasis: { focus: 'adjacency' },
            nodeAlign: 'left',
            nodeWidth: 12,
            nodeGap: 10,
            layoutIterations: 32,
            left: '3%', right: '15%', top: 5, bottom: 5,
            label: { color: '#e8ecf4', fontSize: 10 },
            itemStyle: { borderWidth: 0 },
            lineStyle: { color: 'gradient', curveness: 0.5, opacity: 0.3 },
            data: d.nodes,
            links: d.links
        }]
    };
    chartSankey.setOption(option);
}

function renderGauges() {
    const baseGauge = (value, title, unit, colors) => ({
        backgroundColor: 'transparent',
        series: [{
            type: 'gauge',
            radius: '88%',
            startAngle: 210,
            endAngle: -30,
            min: 0, max: 100,
            progress: { show: true, width: 14, roundCap: true,
                itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [
                    { offset: 0, color: colors[0] }, { offset: 1, color: colors[1] }
                ] } } },
            axisLine: { lineStyle: { width: 14, color: [[1, 'rgba(42,53,96,0.6)']] } },
            pointer: { icon: 'path://', length: '0%' },
            axisTick: { show: false },
            splitLine: { show: false },
            axisLabel: { show: false },
            anchor: { show: false },
            title: {
                offsetCenter: [0, '78%'],
                color: '#8892b0', fontSize: 11, fontWeight: 500
            },
            detail: {
                offsetCenter: [0, '15%'],
                fontSize: 26, fontWeight: 700,
                formatter: '{value}' + unit,
                color: '#e8ecf4'
            },
            data: [{ value: value, name: title }]
        }]
    });

    chartGauge1.setOption(baseGauge(87.4, '跟进率', '%', ['#11998e', '#38ef7d']));
    chartGauge2.setOption(baseGauge(72.3, '目标达成', '%', ['#fa709a', '#fee140']));
}

function renderAlertTable(filter) {
    const alerts = genAlerts(filter || currentAlertFilter);
    const tbody = document.getElementById('alert-table-body');
    if (!tbody) return;

    tbody.innerHTML = alerts.map(a => {
        const valueClass = a.value < 40 ? 'value-low' : a.value < 60 ? 'value-mid' : 'value-high';
        const statusText = { open: '待跟进', acknowledged: '已跟进', snoozed: '暂缓' }[a.status];
        const statusClass = { open: 'status-open', acknowledged: 'status-acknowledged', snoozed: 'status-snoozed' }[a.status];

        return `
            <tr>
                <td><span class="rule-tag rule-${a.rule}">${a.rule} ${a.ruleName}</span></td>
                <td><b>${a.targetName}</b></td>
                <td style="color:#8892b0">${a.city}</td>
                <td>${a.metric}</td>
                <td class="${valueClass}">${a.value}${typeof a.value === 'number' && a.rule === 'R1' ? '%' : ''}</td>
                <td style="color:#8892b0">${a.threshold}${a.rule === 'R1' ? '%' : ''}</td>
                <td><span class="status-pill ${statusClass}">${statusText}</span></td>
                <td style="color:#8892b0">${a.acknowledger || '-'}</td>
                <td style="color:#8892b0; font-size:11px;">${a.ts}</td>
                <td>
                    ${a.status === 'open'
                        ? `<button class="op-btn" onclick="acknowledgeAlert('${a.targetId}')">跟进</button>`
                        : `<button class="op-btn" style="opacity:0.6" disabled>查看</button>`
                    }
                </td>
            </tr>
        `;
    }).join('');
}

function filterAlerts(filter) {
    currentAlertFilter = filter;
    document.querySelectorAll('.alert-filters .filter-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    renderAlertTable(filter);
}

function acknowledgeAlert(id) {
    const btns = document.querySelectorAll('.op-btn');
    const kpiFollow = document.getElementById('kpi-follow-rate');
    const current = parseFloat(kpiFollow.textContent);
    kpiFollow.textContent = Math.min(99.9, current + 0.1).toFixed(1);
    event.target.textContent = '已跟进';
    event.target.style.opacity = 0.6;
    event.target.disabled = true;
}

function switchMode(mode) {
    document.querySelectorAll('.mode-switch .mode-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    if (mode === 'real') {
        const toast = document.createElement('div');
        toast.textContent = '⚠️ 请先在 config 中配置真实 API 凭证';
        toast.style.cssText = 'position:fixed;top:20px;left:50%;transform:translateX(-50%);background:rgba(245,87,108,0.9);color:#fff;padding:10px 20px;border-radius:8px;z-index:9999;font-size:13px;';
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
}

function refreshData() {
    const icon = document.getElementById('refresh-icon');
    icon.classList.add('spinning');

    const kpis = [
        ['kpi-alert-total', () => Math.round(200 + Math.random() * 80)],
        ['kpi-follow-rate', () => (85 + Math.random() * 6).toFixed(1)],
        ['kpi-latency', () => Math.round(40 + Math.random() * 30)],
        ['kpi-goal-rate', () => (68 + Math.random() * 12).toFixed(1)],
        ['kpi-saved-time', () => (14 + Math.random() * 5).toFixed(1)],
    ];

    kpis.forEach(([id, gen], i) => {
        setTimeout(() => {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = gen();
                el.style.transition = 'transform 0.2s';
                el.style.transform = 'scale(1.15)';
                setTimeout(() => el.style.transform = 'scale(1)', 200);
            }
        }, i * 120);
    });

    setTimeout(() => {
        renderTrendChart();
        renderRulePie();
        renderBdmRank(currentBdmFilter);
        renderForecastChart();
        renderHeatmap();
        renderRadar();
        renderSankey();
        renderGauges();
        renderAlertTable();
        icon.classList.remove('spinning');
    }, 500);
}

function exportRecap() {
    const recap = `# 冲锋赛复盘报告

## 核心指标
- 预警总数：246 条
- 已跟进：215 条
- 跟进率：87.4%
- 异常发现时效：47 分钟
- 目标达成率：72.3%

## 规则分布
- R1 低完成率：138 条 (56%)
- R2 增速停滞：58 条 (24%)
- R3 冲刺不足：32 条 (13%)
- R4 层级失衡：18 条 (7%)

## 优化建议
1. R1低完成率预警仍占56%，建议加强日常辅导
2. 关注杭州一区内部分化问题
3. 15-18点设置专属响应窗口

---
*生成时间：${new Date().toLocaleString('zh-CN')}*
`;

    const blob = new Blob([recap], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `冲锋赛复盘报告_${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
}
