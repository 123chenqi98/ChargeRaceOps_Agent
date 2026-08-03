const AI_KNOWLEDGE = {
    bdms: {
        '王鸿鹏': {city: '杭州一区', sr: 5.31, dr: 9.54, sc: 3.2, trend: '↓明显下降', issues: ['POS故障', '新人培训不足']},
        '朱超颖': {city: '杭州一区', sr: 75, dr: 82.5, sc: 68, trend: '↑稳步上升', issues: []},
        '李明':   {city: '杭州二区', sr: 45, dr: 55, sc: 40, trend: '→波动', issues: ['扫码偏低']},
        '张伟':   {city: '绍兴一区', sr: 90, dr: 88, sc: 85, trend: '↑稳定', issues: []},
        '陈静':   {city: '金华一区', sr: 58, dr: 62, sc: 50, trend: '→波动', issues: ['周末冲量乏力']},
        '刘强':   {city: '台州一区', sr: 35, dr: 40, sc: 30, trend: '↓连续落后', issues: ['新人占比高', 'CM培训不足']},
        '黄磊':   {city: '温州一区', sr: 70, dr: 75, sc: 65, trend: '→稳定', issues: ['月末波动']},
        '周婷':   {city: '宁波一区', sr: 82, dr: 78, sc: 80, trend: '↑优秀', issues: ['扫码略低']},
    }
};

function aiMockChat(query) {
    const q = query.trim();
    let bdmName = null;
    for (const name of Object.keys(AI_KNOWLEDGE.bdms)) {
        if (q.includes(name)) { bdmName = name; break; }
    }

    if (/整体|全部|汇总|进度|现状|如何/.test(q) && !bdmName) {
        return overallAnswer();
    }
    if (/复盘|总结|回顾|要点|结论/.test(q)) {
        return recapAnswer();
    }
    if (bdmName && /为什么|为啥|原因|归因/.test(q)) {
        return attributionAnswer(bdmName);
    }
    if (bdmName && /怎么|如何|帮助|达标|提升|办法|建议/.test(q)) {
        return strategyAnswer(bdmName);
    }
    if (bdmName) {
        return metricsAnswer(bdmName);
    }
    return fallbackAnswer();
}

function overallAnswer() {
    return `## 📈 冲锋整体进度快照

### 关键指标
- 👥 **覆盖BDM**：8人 / 30名CM
- 🎯 **综合平均达成**：**68.5%**（目标 100%）
- ⏱️ **异常发现平均时效**：**47 分钟**
- 🔔 **今日预警总数**：126 条（已跟进 **87.4%**）

### 🏆 TOP3 BDM
1. 张伟（92.5%）- 经验可复制标杆
2. 朱超颖（90.1%）
3. 周婷（88.3%）

### ⚠️ BOTTOM3（需重点关注）
1. 王鸿鹏（15.3%）
2. 刘强（32.8%）
3. 李明（46.7%）

### 🧭 当前建议
⚠️ BOTTOM3 需立刻安排支援，15点后盯紧 R4 内部分化，19点后启动 R3 尾段冲刺策略`;
}

function recapAnswer() {
    return `## 📝 复盘要点（AI 自动总结）

### ✅ 亮点
1. **预警跟进率 87.4%**，超目标 2.4 pct，状态机闭环有效
2. **异常发现时效 47min**，较人工 +87%
3. 张伟连续3轮Top2，打法已沉淀为《优秀BDM手册》

### ⚠️ 待改进
1. **R1 低完成率占比 56%**，日常辅导/目标拆解需前置
2. 王鸿鹏、刘强**连续3场落后**，建议专项提升
3. 15-18点预警响应最慢，建议设专属响应窗口

### 🧪 TOP 归因（出现频次）
1. 目标拆解不合理（32%）→ 下轮提前3天做CM一对一确认
2. POS/系统故障（25%）→ 申请备用核销码
3. 新人培训滞后（18%）→ 老带新结对机制

### 🎯 下轮OKR建议
- O1：BDM综合达成均值 ≥ 90%
- O2：预警跟进率 ≥ 90%
- O3：R1占比 ≤ 45%`;
}

function attributionAnswer(name) {
    const b = AI_KNOWLEDGE.bdms[name];
    let extra = '';
    if (b.issues && b.issues.length) {
        extra = `\n- 已知共性问题：${b.issues.join('、')}\n`;
    }
    let topReasons;
    if (name === '刘强' || name === '王鸿鹏') {
        topReasons = `
| # | 可能原因 | 置信度 |
|---|---------|--------|
| 1 | 目标拆解未对齐，CM和BDM预期不一致 | 92% |
| 2 | 新人培训不足，CM熟练度低 | 83% |
| 3 | POS/核销流程临时故障 | 78% |
| 4 | 销售支持资源倾斜不够 | 52% |`;
    } else if (b.sr < 60) {
        topReasons = `
| # | 可能原因 | 置信度 |
|---|---------|--------|
| 1 | 午/晚高峰人手不足 | 76% |
| 2 | 大客户周末激励未触达 | 65% |
| 3 | 头部门店突发问题 | 58% |`;
    } else {
        topReasons = `
| # | 可能原因 | 置信度 |
|---|---------|--------|
| 1 | 过程中部分时段冲量不够 | 70% |
| 2 | 内部分化（CM差距）开始显现 | 55% |`;
    }
    return `## 🔍 归因分析：${name}（${b.city}）

### 基线画像
- **历史单计均值**：${b.sr}%，**双计**：${b.dr}%，**扫码**：${b.sc}%
- **近期趋势**：${b.trend}${extra}
### TOP 根因分析${topReasons}

> 💡 以上基于规则知识库 + 历史数据基线，仅供参考，最终请以实际业务为准`;
}

function strategyAnswer(name) {
    const b = AI_KNOWLEDGE.bdms[name];
    const trendUp = /↑/.test(b.trend);
    const trendBad = /↓/.test(b.trend);

    const immediate = trendBad
        ? [`15:00前 梳理TOP10未核销门店清单，**逐个电话确认**`,
           `17:00前 对落后CM进行 1v1 指导，重点双计扫码核销`,
           `20:00前 联动销售支持晚高峰驻店支援`]
        : [`15点前拉一次缺口清单，重点盯着后30%CM`,
           `19点启动"冲刺3小时"专项，盯住TOP5门店`];

    const mid = b.issues && b.issues.length
        ? b.issues.map(i => `对「${i}」问题专项：联系对应职能同学（商户运营/培训），本周落地解决`)
        : [`复制张伟/朱超颖打法：午/晚高峰驻TOP5门店支援`];

    return `## 💡 达标策略建议：${name}（${b.city}）
### 🎯 当前状态：${b.trend}
- 单计${b.sr}%，双计${b.dr}%，扫码${b.sc}%

### ⚡ 即时止血（今天内）
${immediate.map(i => `• ${i}`).join('\n')}

### 🏃 中期追赶（冲锋剩余日）
• ${mid.join('\n• ')}
• 大客户资源再分配，向落后CM倾斜可用头部门店
• 电话攻关犹豫未决的大客户

### 🔒 长期优化（下场冲锋前）
1. 提前3天做目标拆解，和每位CM确认可达成范围
2. 建立"时段达成预警"机制，提前1天发现异常苗头
3. 每周一次优秀CM经验分享，横向复制

> 预计拉升完成度 **5-8 pct**，加油 💪`;
}

function metricsAnswer(name) {
    const b = AI_KNOWLEDGE.bdms[name];
    const avg = ((b.sr + b.dr + b.sc) / 3).toFixed(1);
    const diff = Math.round((Math.random() * 30 - 15) * 10) / 10;
    const trendSym = diff > 2 ? '↑' : diff < -2 ? '↓' : '→';
    const color = diff > 2 ? '#38ef7d' : diff < -2 ? '#f5576c' : '#8892b0';

    const hrs = ['09:00', '12:00', '14:00', '当前'];
    const trend = hrs.map((h, i) => {
        const v = Math.max(0, Math.round(b.sr - 15 + i * 5 + (Math.random() * 4 - 2)));
        return `${h} <b>${v}%</b>`;
    }).join(' → ');

    const r1 = b.sr < 60 ? '✅已触发' : '❌未触发';
    const r2 = Math.random() < 0.3 ? '✅已触发' : '❌未触发';
    const r3 = avg < 70 ? '✅已触发' : '❌未触发';

    return `## 📊 ${name}（${b.city}）实时数据快照

### 当前指标
| 指标 | 当前 | 历史基线 | 环比 |
|------|------|---------|------|
| 单计核销完成度 | **${b.sr}%** | ${Math.max(b.sr - diff, 0)}% | <span style="color:${color}">${trendSym}${Math.abs(diff)}pct</span> |
| 双计核销完成度 | **${b.dr}%** | ${Math.max(b.dr - diff, 0)}% | - |
| 双计扫码完成度 | **${b.sc}%** | ${Math.max(b.sc - diff, 0)}% | - |
| 综合达成 | **${avg}%** | - | ${trendSym} |

### 近 6 小时趋势
${trend}
- **增速评估**：${avg < 60
        ? '偏慢，建议立刻按标准动作清单执行'
        : avg < 85
            ? '正常，按当前节奏推进'
            : '优秀，可把经验整理输出给落后同学'}

### 今日关联预警
- R1 低完成率：<b>${r1}</b>
- R2 增速停滞：<b>${r2}</b>
- R3 冲刺不足：<b>${r3}</b>`;
}

function fallbackAnswer() {
    return `我可以帮你：

**📊 查数类**
例：王鸿鹏现在进度如何？ / 整体冲锋进度怎么样？

**🧐 归因类**
例：为什么刘强低完成率？ / R3 预警通常什么原因？

**💡 策略类**
例：怎么帮陈静达标？ / 针对增速停滞的建议？

**📝 复盘类**
例：给我本场冲锋的复盘要点 / 下轮冲锋OKR建议

描述越具体，我给出的回答越有针对性～`;
}

function appendMsg(text, role) {
    const body = document.getElementById('ai-chat-body');
    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble ' + (role === 'user' ? 'msg-user' : 'msg-ai');
    bubble.innerHTML = text
        .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
        .replace(/```([\s\S]*?)```/g, '<code>$1</code>')
        .replace(/^### (.*?)$/gm, (_, g1) => `<div style="font-weight:700;font-size:13px;color:#4facfe;margin:6px 0 2px;">${g1}</div>`)
        .replace(/^## (.*?)$/gm, (_, g1) => `<div style="font-weight:700;font-size:14px;margin:6px 0 4px;background:linear-gradient(135deg,#fff,#a8c0ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">${g1}</div>`)
        .replace(/^# (.*?)$/gm, (_, g1) => `<div style="font-weight:800;font-size:15px;margin:6px 0;">${g1}</div>`)
        .replace(/^[-•] /gm, '▸ ')
        .replace(/\n/g, '<br/>');
    body.appendChild(bubble);
    body.scrollTop = body.scrollHeight;
    return bubble;
}

function appendTyping() {
    const body = document.getElementById('ai-chat-body');
    const t = document.createElement('div');
    t.className = 'msg-bubble msg-ai';
    t.id = 'ai-typing';
    t.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
    body.appendChild(t);
    body.scrollTop = body.scrollHeight;
    return t;
}

function sendAiMsg() {
    const input = document.getElementById('ai-input');
    const query = input.value.trim();
    if (!query) return;
    appendMsg(query, 'user');
    input.value = '';

    const typing = appendTyping();

    setTimeout(() => {
        typing.remove();
        const answer = aiMockChat(query);
        appendMsg(answer, 'ai');
    }, 650 + Math.random() * 500);
}

function aiQuickAsk(q) {
    document.getElementById('ai-input').value = q;
    sendAiMsg();
}

function toggleAiPanel() {
    const panel = document.getElementById('ai-panel');
    panel.classList.toggle('open');
    if (panel.classList.contains('open')) {
        const body = document.getElementById('ai-chat-body');
        if (body.childElementCount === 0) {
            const welcome = `你好！我是冲锋赛 **AI数据助手** 🧠

我能做这些事：
• 📊 问数：王鸿鹏现在进度如何？
• 🧠 归因：为什么刘强低完成率？
• 💡 策略：怎么帮陈静达标？
• 📝 复盘：给我本场冲锋复盘要点

试试点击下方快捷问题，或直接输入你的问题 👇`;
            appendMsg(welcome, 'ai');
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {
    // 面板默认关闭
});
