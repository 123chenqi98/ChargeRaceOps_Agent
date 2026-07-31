const MOCK_BDMS = [
    { id: 'bdm_001', name: '王鸿鹏', city: '杭州一区' },
    { id: 'bdm_002', name: '朱超颖', city: '杭州一区' },
    { id: 'bdm_003', name: '李明',   city: '杭州二区' },
    { id: 'bdm_004', name: '张伟',   city: '绍兴一区' },
    { id: 'bdm_005', name: '陈静',   city: '金华一区' },
    { id: 'bdm_006', name: '刘强',   city: '台州一区' },
    { id: 'bdm_007', name: '黄磊',   city: '温州一区' },
    { id: 'bdm_008', name: '周婷',   city: '宁波一区' },
];

const MOCK_CITIES = ['杭州一区', '杭州二区', '绍兴一区', '金华一区', '台州一区', '温州一区', '宁波一区', '嘉兴一区'];

function genTrendData() {
    const hours = [];
    const now = new Date();
    for (let i = 71; i >= 0; i--) {
        const d = new Date(now.getTime() - i * 3600000);
        hours.push(`${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:00`);
    }

    const genSeries = (base, variance, spikeChance = 0.1) => {
        return hours.map((_, i) => {
            let v = base + Math.random() * variance * 2 - variance;
            if (Math.random() < spikeChance) v += Math.random() * variance * 2;
            if (i > 9 && i < 22) v *= 1.1;
            if (i > 33 && i < 46) v *= 1.05;
            if (i > 57 && i < 70) v *= 1.15;
            return Math.max(0, Math.round(v));
        });
    };

    return {
        times: hours,
        R1: genSeries(6, 4),
        R2: genSeries(2.5, 2.5, 0.05),
        R3: genSeries(1.8, 1.8, 0.08),
        R4: genSeries(0.8, 1, 0.03),
    };
}

function genRuleDist() {
    return [
        { value: 138, name: 'R1 低完成率', itemStyle: { color: '#f5576c' } },
        { value: 58,  name: 'R2 增速停滞', itemStyle: { color: '#ffa751' } },
        { value: 32,  name: 'R3 冲刺不足', itemStyle: { color: '#4facfe' } },
        { value: 18,  name: 'R4 层级失衡', itemStyle: { color: '#a855f7' } },
    ];
}

function genBdmRankData(type = 'single') {
    const dataSet = {
        single: [
            ['王鸿鹏', 5.3], ['刘强', 35.0], ['陈静', 58.0], ['李明', 45.0],
            ['黄磊', 70.0], ['周婷', 82.0], ['朱超颖', 75.0], ['张伟', 90.0],
        ],
        double: [
            ['王鸿鹏', 9.5], ['刘强', 40.0], ['陈静', 62.0], ['李明', 55.0],
            ['黄磊', 75.0], ['周婷', 78.0], ['朱超颖', 82.5], ['张伟', 88.0],
        ],
        scan: [
            ['王鸿鹏', 3.2], ['刘强', 30.0], ['陈静', 50.0], ['李明', 40.0],
            ['黄磊', 65.0], ['周婷', 80.0], ['朱超颖', 68.0], ['张伟', 85.0],
        ],
        comprehensive: [
            ['王鸿鹏', 6.0], ['刘强', 35.0], ['陈静', 56.7], ['李明', 46.7],
            ['黄磊', 70.0], ['周婷', 80.0], ['朱超颖', 75.2], ['张伟', 87.7],
        ],
    };

    const data = dataSet[type].sort((a, b) => a[1] - b[1]);
    const names = data.map(d => d[0]);
    const values = data.map(d => d[1]);

    return { names, values };
}

function genForecastData() {
    const times = [];
    const now = new Date();
    for (let i = 0; i < 24; i++) {
        const d = new Date(now.getTime() - (12 - i) * 3600000);
        times.push(`${String(d.getHours()).padStart(2, '0')}:00`);
    }

    const actual = [];
    const predicted = [];
    const target = 100;

    for (let i = 0; i < 24; i++) {
        if (i <= 12) {
            const a = 10 + i * 4.8 + Math.random() * 4;
            actual.push(Math.min(target, a));
            predicted.push(null);
        } else {
            actual.push(null);
            const p = actual[12] + (i - 12) * 3.2 + Math.random() * 2;
            predicted.push(Math.min(target, p));
        }
    }

    return { times, actual, predicted, target };
}

function genHeatmapData() {
    const cmCount = 6;
    const data = [];
    const xLabels = [];
    const yLabels = MOCK_BDMS.map(b => b.name);

    for (let j = 0; j < cmCount; j++) {
        xLabels.push(`CM${j + 1}`);
    }

    for (let i = 0; i < yLabels.length; i++) {
        for (let j = 0; j < cmCount; j++) {
            let val;
            if (i === 0) val = Math.random() * 40 + 10;
            else if (i === 5) val = Math.random() * 30 + 20;
            else if (j === 0) val = Math.random() * 30 + 30;
            else if (j === 5) val = Math.random() * 40 + 50;
            else val = Math.random() * 50 + 40;
            data.push([j, i, Math.round(val)]);
        }
    }

    return { xLabels, yLabels, data };
}

function genRadarData() {
    const indicators = [
        { name: '单计完成度', max: 100 },
        { name: '双计完成度', max: 100 },
        { name: '扫码完成度', max: 100 },
        { name: '增速稳定', max: 100 },
        { name: '响应速度', max: 100 },
        { name: '团队均衡', max: 100 },
    ];

    const top5 = ['张伟', '朱超颖', '周婷', '黄磊', '陈静'];
    const colors = ['#4facfe', '#38ef7d', '#fbbf24', '#a855f7', '#22d3ee'];

    return {
        indicators,
        series: top5.map((name, i) => ({
            name,
            value: [
                70 + Math.random() * 25,
                65 + Math.random() * 25,
                60 + Math.random() * 30,
                60 + Math.random() * 35,
                55 + Math.random() * 35,
                50 + Math.random() * 40,
            ].map(v => Math.round(v)),
            itemStyle: { color: colors[i] },
            areaStyle: { opacity: 0.15 },
            lineStyle: { width: 2 },
        })),
    };
}

function genSankeyData() {
    return {
        nodes: [
            { name: 'R1 低完成率', itemStyle: { color: '#f5576c' } },
            { name: 'R2 增速停滞', itemStyle: { color: '#ffa751' } },
            { name: 'R3 冲刺不足', itemStyle: { color: '#4facfe' } },
            { name: 'R4 层级失衡', itemStyle: { color: '#a855f7' } },
            { name: '待跟进 (31)' },
            { name: '已跟进 (200)' },
            { name: '暂缓 (15)' },
            { name: '已过期 (12)' },
        ],
        links: [
            { source: 'R1 低完成率', target: '已跟进 (200)', value: 110 },
            { source: 'R1 低完成率', target: '待跟进 (31)', value: 20 },
            { source: 'R1 低完成率', target: '已过期 (12)', value: 8 },
            { source: 'R2 增速停滞', target: '已跟进 (200)', value: 48 },
            { source: 'R2 增速停滞', target: '暂缓 (15)', value: 10 },
            { source: 'R3 冲刺不足', target: '已跟进 (200)', value: 28 },
            { source: 'R3 冲刺不足', target: '待跟进 (31)', value: 4 },
            { source: 'R4 层级失衡', target: '已跟进 (200)', value: 14 },
            { source: 'R4 层级失衡', target: '暂缓 (15)', value: 4 },
        ],
    };
}

function genAlerts(filter = 'all') {
    const rules = ['R1', 'R2', 'R3', 'R4'];
    const ruleNames = { R1: '低完成率', R2: '增速停滞', R3: '冲刺不足', R4: '层级失衡' };
    const metrics = ['单计核销', '双计核销', '双计扫码', '综合达成'];
    const statuses = ['open', 'acknowledged', 'acknowledged', 'acknowledged', 'acknowledged'];
    const users = ['陈琦', '朱超颖', '销售支持A', '销售支持B', '销售支持C'];

    const alerts = [];
    const now = new Date();

    for (let i = 0; i < 50; i++) {
        const bdm = MOCK_BDMS[Math.floor(Math.random() * MOCK_BDMS.length)];
        const rule = rules[Math.floor(Math.random() * rules.length)];
        const metric = metrics[Math.floor(Math.random() * metrics.length)];
        const status = statuses[Math.floor(Math.random() * statuses.length)];

        let threshold = rule === 'R1' ? 60 : rule === 'R2' ? 2 : rule === 'R3' ? 0 : 40;
        let value = rule === 'R1'
            ? (Math.random() * 55 + 5)
            : rule === 'R2'
                ? Math.floor(Math.random() * 5 + 2)
                : rule === 'R3'
                    ? (Math.random() * 30 + 10)
                    : (Math.random() * 30 + 45);

        if (filter === 'open' && status !== 'open') continue;
        if (filter === 'acknowledged' && status !== 'acknowledged') continue;

        alerts.push({
            rule,
            ruleName: ruleNames[rule],
            targetId: bdm.id,
            targetName: bdm.name,
            city: bdm.city,
            metric,
            value: Math.round(value * 10) / 10,
            threshold,
            status,
            acknowledger: status === 'acknowledged' ? users[Math.floor(Math.random() * users.length)] : null,
            ts: new Date(now.getTime() - Math.floor(Math.random() * 3600000 * 10)).toLocaleString('zh-CN', { hour12: false }),
        });
    }

    return alerts.slice(0, filter === 'all' ? 50 : filter === 'open' ? 31 : 215);
}
