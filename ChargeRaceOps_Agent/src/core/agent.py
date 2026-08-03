"""
AI 数据分析助手 Agent

支持两种模式：
1. LLM 模式：接入大模型 API（字节豆包 / OpenAI 兼容格式），做真正的自然语言问答
2. 规则模拟模式：内置 Prompt 模板 + 关键词匹配 + 数据分析逻辑，无 API 也可演示完整交互

核心能力：
- 自然语言问数："王鸿鹏最近3小时完成度如何？" -> 返回结构化答案
- 归因分析："为什么刘强低完成率？" -> 自动归因
- 策略推荐："怎么帮陈静达标？" -> 给出行动建议
- 复盘生成："给我本场冲锋的复盘要点"
"""

import json
import re
import random
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

try:
    import requests
except ImportError:
    requests = None


class AIAnalysisAgent:
    """冲锋赛数据 AI 分析助手"""

    def __init__(self, llm_provider: str = "mock", api_key: str = "", base_url: str = ""):
        self.provider = llm_provider
        self.api_key = api_key
        self.base_url = base_url
        self.history = []

        self.bdm_baseline = {
            '王鸿鹏': {'城市': '杭州一区', '单计均值': 78.2, '双计均值': 82.1, '近期趋势': '↓下降明显', '历史问题': ['多次出现增速停滞', '重点门店POS故障']},
            '刘强': {'城市': '台州一区', '单计均值': 72.0, '双计均值': 76.0, '近期趋势': '↓连续多轮落后', '历史问题': ['CM培训不足', '新人占比高']},
            '陈静': {'城市': '金华一区', '单计均值': 80.0, '双计均值': 81.5, '近期趋势': '→波动', '历史问题': ['周末冲量乏力', '连锁客户维护不够']},
            '李明': {'城市': '杭州二区', '单计均值': 80.0, '双计均值': 82.0, '近期趋势': '↑稳步提升', '历史问题': ['扫码核销偏低']},
            '张伟': {'城市': '绍兴一区', '单计均值': 91.5, '双计均值': 92.0, '近期趋势': '↑稳定', '历史问题': []},
            '朱超颖': {'城市': '杭州一区', '单计均值': 88.0, '双计均值': 90.0, '近期趋势': '↑优秀', '历史问题': []},
            '周婷': {'城市': '宁波一区', '单计均值': 87.0, '双计均值': 86.0, '近期趋势': '→良好', '历史问题': ['双计扫码略低']},
            '黄磊': {'城市': '温州一区', '单计均值': 83.0, '双计均值': 84.0, '近期趋势': '→稳定', '历史问题': ['月末冲量波动']},
        }

        self.rule_knowledge = {
            'R1': {'名称': '低完成率预警',
                   '常见原因': ['目标拆解不合理', '门店覆盖不足', '新人培训滞后', 'POS/系统故障', '重点客户临时取消'],
                   '标准动作': ['立即核对门店TOP10未核销清单', '确认是否有POS或系统故障', '对落后CM进行1v1复盘', '调用销售支持支援重点门店']},
            'R2': {'名称': '增速停滞预警',
                   '常见原因': ['POS系统故障', '午间/高峰时段人员不足', '头部门店突发情况', '核销流程中断', '时段策略失效'],
                   '标准动作': ['优先排查TOP3门店核销异常', '联系商户运营确认POS状态', '安排CM在高峰时段驻店支援', '调整晚高峰激励策略']},
            'R3': {'名称': '冲刺不足预警',
                   '常见原因': ['剩余可用门店不足', '客户消耗意愿降低', '尾段策略缺失', '冲刺激励力度不够'],
                   '标准动作': ['启动"尾段冲刺"专项策略', 'TOP10门店逐一电话确认', '追加临时核销激励', '联动销售支持全员驻点']},
            'R4': {'名称': '层级失衡预警',
                   '常见原因': ['个别新人CM跟不上节奏', '老客户资源分配不均', 'BDM精力分配失衡', '个别门店长期出问题'],
                   '标准动作': ['把TOP差CM与TOP好CM结对帮扶', '重新分配大客户资源', 'BDM重点辅导落后门店', '启动新人专项培训']},
        }

        self.dialog_prompts = {
            'hello': ['你好！我是冲锋赛AI数据助手 🧠\n\n我可以帮你：\n• 自然语言查询数据（如：王鸿鹏现在进度如何？）\n• 异常归因分析（如：为什么刘强低完成率？）\n• 行动策略推荐（如：帮陈静达标有什么建议？）\n• 复盘要点总结（如：给我本场冲锋的复盘要点）\n\n请输入你的问题，或点击下方快捷问题 👇'],
            'error': ['抱歉，我暂时无法理解这个问题，请换一种描述方式试试～',
                      '嗯，这个问题超出我的知识库了，可以描述得更具体一点吗？比如加上BDM名字或规则名称～'],
        }

    def chat(self, user_input: str, extra_data: dict = None) -> dict:
        """对外暴露的对话接口"""
        user_input = user_input.strip()
        if not user_input:
            return self._build_reply(random.choice(self.dialog_prompts['hello']), type='text')

        logger.info(f"[AI Agent] 用户输入: {user_input}")

        if self.provider == "mock" or not self.api_key:
            answer = self._rule_chat(user_input, extra_data or {})
        else:
            answer = self._llm_chat(user_input, extra_data or {})

        self.history.append({'role': 'user', 'content': user_input})
        self.history.append({'role': 'assistant', 'content': answer['content']})
        return answer

    # ========== 规则模式：核心逻辑 ==========

    def _rule_chat(self, query: str, extra: dict) -> dict:
        q = query

        bdm = self._extract_bdm(q)
        rule_id = self._extract_rule(q)
        intent = self._detect_intent(q)

        if intent == '归因' and (bdm or rule_id):
            return self._build_reply(self._generate_attribution(bdm, rule_id), type='markdown',
                                    data={'bdm': bdm, 'rule_id': rule_id, 'intent': 'attribution'})

        if intent == '策略推荐' and bdm:
            return self._build_reply(self._generate_strategy(bdm), type='markdown',
                                    data={'bdm': bdm, 'intent': 'strategy'})

        if intent == '查数' and bdm:
            return self._build_reply(self._generate_bdm_metrics(bdm, extra), type='markdown',
                                    data={'bdm': bdm, 'intent': 'metrics'})

        if intent == '查数' and ('整体' in q or '全部' in q or '汇总' in q or '总结' in q):
            return self._build_reply(self._generate_overall_summary(extra), type='markdown',
                                    data={'intent': 'summary'})

        if intent == '复盘':
            return self._build_reply(self._generate_recap_summary(extra), type='markdown',
                                    data={'intent': 'recap'})

        if bdm:
            return self._build_reply(self._generate_bdm_intro(bdm), type='markdown',
                                    data={'bdm': bdm, 'intent': 'profile'})

        if '你好' in q or 'hi' in q.lower() or 'hello' in q.lower():
            return self._build_reply(random.choice(self.dialog_prompts['hello']), type='text')

        return self._build_reply(
            '我可以帮你做这些：\n\n'
            '**📊 查数类**\n'
            '  例：王鸿鹏现在进度如何？\n'
            '  例：整体冲锋进度怎么样？\n\n'
            '**🧐 归因类**\n'
            '  例：为什么刘强低完成率？\n'
            '  例：R3预警通常是什么原因？\n\n'
            '**💡 策略类**\n'
            '  例：怎么帮陈静达标？\n'
            '  例：针对增速停滞有什么建议？\n\n'
            '**📝 复盘类**\n'
            '  例：给我本场冲锋的复盘要点',
            type='markdown'
        )

    def _generate_attribution(self, bdm: str, rule_id: str) -> str:
        parts = [f"## 🔍 归因分析：{bdm or rule_id or '综合'}"]
        if bdm:
            b = self.bdm_baseline.get(bdm, {})
            if b:
                parts.append(f"\n### 🧑‍💼 {bdm}（{b.get('城市', '')}）基线画像")
                parts.append(f"- 历史**单计**均值：{b.get('单计均值', 'N/A')}%")
                parts.append(f"- 历史**双计**均值：{b.get('双计均值', 'N/A')}%")
                parts.append(f"- 近期趋势：{b.get('近期趋势', '→正常')}")
                if b.get('历史问题'):
                    parts.append(f"- 已知共性问题：{'、'.join(b['历史问题'])}")

        if rule_id:
            r = self.rule_knowledge.get(rule_id, {})
            parts.append(f"\n### 📌 触发规则：{rule_id}「{r.get('名称', '')}」")
            parts.append(f"**🌟 常见原因（按频次排序）：**")
            for i, c in enumerate(r.get('常见原因', []), 1):
                parts.append(f"{i}. {c}")
            parts.append(f"\n**✅ 推荐标准动作：**")
            for i, a in enumerate(r.get('标准动作', []), 1):
                parts.append(f"{i}. {a}")

        if not bdm and not rule_id:
            parts.append("请描述具体BDM名称或规则编号，我可以给出更精准的归因～")

        parts.append('\n> 💡 以上分析基于历史数据基线 + 规则知识库，仅供参考，最终决策请结合当周实际情况判断')
        return '\n'.join(parts)

    def _generate_strategy(self, bdm: str) -> str:
        b = self.bdm_baseline.get(bdm, {})
        parts = [f"## 💡 达标策略建议：{bdm}"]
        if not b:
            return f"暂无 {bdm} 的数据，请先在数据集中录入对应BDM。"

        trend = b.get('近期趋势', '')
        problems = b.get('历史问题', [])

        parts.append(f"\n### 🎯 当前状态：{trend}")
        parts.append(f"- 单计基线 {b.get('单计均值', '?')}%，双计基线 {b.get('双计均值', '?')}%")

        if trend.startswith('↓'):
            parts.append("\n### ⚡ 即时止血（今天内完成）")
            parts.append("1. **15:00前** 梳理TOP10未核销门店清单，逐一电话确认")
            parts.append("2. **17:00前** 对落后CM进行1v1指导，重点看双计扫码核销")
            parts.append("3. **20:00前** 联动销售支持进行晚高峰驻店支援")

        parts.append("\n### 🏃 中期追赶（本场冲锋剩余日）")
        if 'POS' in str(problems) or '故障' in str(problems):
            parts.append("1. 联系商户运营排查POS故障，申请临时备用核销码")
        if '新人' in str(problems) or '培训' in str(problems):
            parts.append("1. 给新人CM安排优秀CM结对，设置当日冲刺陪跑")
        if '资源' in str(problems) or '分配' in str(problems):
            parts.append("1. 重新梳理大客户资源分配方案，向落后CM倾斜头部门店")
        if len(problems) == 0:
            parts.append("1. 复制张伟/朱超颖的成功打法：午间和晚高峰驻TOP5门店支援")
            parts.append("2. 针对连锁客户，申请当日临时核销激励")

        parts.append("\n### 🔒 长期优化（下一场冲锋前）")
        parts.append("1. 提前3天做目标拆解，和每个CM确认可达成范围")
        parts.append("2. 建立'时段达成预警'，提前1天发现异常苗头")
        parts.append("3. 每周组织优秀CM经验分享会，横向复制")
        parts.append("\n> 预计可拉升完成度 **5-8 pct**，加油 💪")

        return '\n'.join(parts)

    def _generate_bdm_metrics(self, bdm: str, extra: dict) -> str:
        b = self.bdm_baseline.get(bdm, {})
        s_rate = extra.get('single_rate', round(random.uniform(5, 95), 1))
        d_rate = extra.get('double_rate', round(random.uniform(5, 95), 1))
        sc_rate = extra.get('scan_rate', round(random.uniform(3, 90), 1))
        compr = round((s_rate + d_rate + sc_rate) / 3, 1)
        diff = round(random.uniform(-15, 15), 1)
        diff_symbol = '↑' if diff > 2 else ('↓' if diff < -2 else '→')

        return f"""## 📊 {bdm}（{b.get('城市', '未知')}）实时数据

### 当前指标快照
| 指标 | 当前 | 历史基线 | 对比 |
|------|------|---------|------|
| 单计核销完成度 | **{s_rate}%** | {b.get('单计均值', '?')}% | {diff_symbol}{abs(diff)} pct |
| 双计核销完成度 | **{d_rate}%** | {b.get('双计均值', '?')}% | {diff_symbol}{abs(diff/2)} pct |
| 双计扫码完成度 | **{sc_rate}%** | {round(b.get('双计均值',80)*0.9,1)}% | {diff_symbol}{abs(diff/3)} pct |
| 综合达成 | **{compr}%** | - | {diff_symbol}{abs(diff)} pct |

### 时间趋势（近6小时）
- 09:00 {max(0,s_rate-20)}% → 12:00 {max(0,s_rate-10)}% → 14:00 {max(0,s_rate-5)}% → **当前 {s_rate}%**
- **增速评估**：{'偏慢，建议启动R2排查' if s_rate < 60 else '正常，保持节奏' if s_rate < 85 else '优秀，可作为标杆输出经验'}

### 关联预警（今日）
- R1 低完成率：{'✅ 已触发' if s_rate < 60 else '❌ 未触发'}
- R2 增速停滞：{'✅ 已触发' if random.random() < 0.3 else '❌ 未触发'}
- R3 冲刺不足：{'✅ 已触发' if compr < 70 else '❌ 未触发'}

> 💡 建议：{'请立即点击「跟进」并执行标准动作清单' if compr < 60 else '按当前节奏推进即可，注意20:00后冲刺时段'}"""

    def _generate_overall_summary(self, extra: dict) -> str:
        total = extra.get('total_alerts', 126)
        ack_rate = extra.get('ack_rate', 85.2)
        avg_compr = extra.get('avg_compr', 68.5)
        top3 = [('张伟', 92.5), ('朱超颖', 90.1), ('周婷', 88.3)]
        bot3 = [('王鸿鹏', 15.3), ('刘强', 32.8), ('李明', 46.7)]

        lines = [
            "## 📈 冲锋整体进度快照",
            "",
            "### 关键指标",
            f"- 👥 **覆盖BDM**：8人 / 30名CM",
            f"- 🎯 **综合平均达成**：{avg_compr}%（目标 100%）",
            f"- ⏱️ **异常发现平均时效**：{extra.get('latency',47)} 分钟",
            f"- 🔔 **今日预警总数**：{total} 条（已跟进 {ack_rate}%）",
            "",
            "### 🏆 TOP3 BDM",
            f"1. {top3[0][0]}（{top3[0][1]}%）- 经验可复制标杆",
            f"2. {top3[1][0]}（{top3[1][1]}%）",
            f"3. {top3[2][0]}（{top3[2][1]}%）",
            "",
            "### ⚠️ BOTTOM3 BDM（需重点关注）",
            f"1. {bot3[0][0]}（{bot3[0][1]}%）",
            f"2. {bot3[1][0]}（{bot3[1][1]}%）",
            f"3. {bot3[2][0]}（{bot3[2][1]}%）",
            "",
            "### 🧭 当前阶段建议",
            f"- {'⚠️ 立即关注BOTTOM3，安排支援' if avg_compr < 75 else '✅ 整体正常，重点关注后20%的掉队情况' }",
            "- 15:00 后盯紧 R4（层级失衡）避免内部分化",
            "- 19:00 后盯紧 R3（冲刺不足）提前准备尾段冲刺",
        ]
        return '\n'.join(lines)

    def _generate_recap_summary(self, extra: dict) -> str:
        return """## 📝 冲锋复盘要点（AI 自动总结）

### ✅ 亮点
1. **预警跟进率 87.4%**，超过目标值 2.4 pct，状态机闭环有效
2. **异常发现时效 47 分钟**，较人工模式提升 87%，小时级数据闭环跑通
3. BDM **张伟**连续3轮冲锋Top2，经验已整理为《优秀BDM打法手册》

### ⚠️ 待改进
1. R1 低完成率预警仍占 **56%**，说明日常辅导和目标拆解环节有改进空间
2. 王鸿鹏、刘强两名BDM连续 **3场**冲锋排名后两位，建议专项提升计划
3. 15:00-18:00 时段预警响应最慢，建议设置**专属响应窗口**并安排专人值守

### 🧪 归因（Top原因）
1. 目标拆解不合理（32%）- 下轮提前3天和CM确认可达成范围
2. POS/系统故障（25%）- 申请备用核销码机制
3. 新人CM培训滞后（18%）- 建立「优秀+新人」结对机制

### 🎯 下轮OKR（建议）
- O1：BDM综合达成均值 ≥ 90%
- O2：预警跟进率 ≥ 90%
- O3：R1 低完成率预警占比 ≤ 45%
- O4：无连续3场落后的BDM
"""

    def _generate_bdm_intro(self, bdm: str) -> str:
        b = self.bdm_baseline.get(bdm, {})
        if not b:
            return f"暂无 {bdm} 的基线数据，你可以问：\n• 整体进度\n• {bdm}现在完成度\n• 为什么{bdm}完成度低？"
        return f"""## 🧑‍💼 {bdm} 画像速览

| 项目 | 详情 |
|------|------|
| 所属城市 | {b.get('城市','-')} |
| 历史单计均值 | {b.get('单计均值','-')}% |
| 历史双计均值 | {b.get('双计均值','-')}% |
| 近期趋势 | {b.get('近期趋势','-')} |
| 已知共性问题 | {'、'.join(b.get('历史问题',['暂无'])) or '暂无'} |

👉 你可以继续问我：
• "{bdm}现在完成度如何？"
• "为什么{bdm}完成度低？"
• "怎么帮{bdm}达标？"
"""

    # ========== 辅助方法 ==========

    def _extract_bdm(self, s: str) -> Optional[str]:
        for name in self.bdm_baseline.keys():
            if name in s:
                return name
        return None

    def _extract_rule(self, s: str) -> Optional[str]:
        for r in ['R1', 'R2', 'R3', 'R4']:
            if r in s or self.rule_knowledge[r]['名称'] in s:
                return r
        return None

    def _detect_intent(self, s: str) -> str:
        s = s.lower()
        if any(k in s for k in ['为什么', '原因', '归因', '为啥', '导致']):
            return '归因'
        if any(k in s for k in ['怎么', '如何', '建议', '策略', '帮', '达标', '提升', '办法']):
            return '策略推荐'
        if any(k in s for k in ['复盘', '总结', '回顾', '要点', '结论']):
            return '复盘'
        if any(k in s for k in ['多少', '如何', '进度', '数据', '完成度', '怎么样', '查', '汇总', '整体', '快照', '现状']):
            return '查数'
        return '查数'

    def _build_reply(self, content: str, type: str = 'markdown', data: dict = None) -> dict:
        return {
            'content': content,
            'type': type,
            'data': data or {},
            'ts': datetime.now().isoformat(),
            'provider': self.provider,
        }

    # ========== LLM 模式（可选接入真实大模型）==========

    def _llm_chat(self, query: str, extra: dict) -> dict:
        if not requests or not self.api_key:
            return self._build_reply('LLM API 未配置，使用规则模式', type='text')

        system_prompt = f"""你是「冲锋赛过程管理」AI助手，服务于生活服务东部大区销售支持团队。
你掌握以下业务知识：
- 4条预警规则: {json.dumps(self.rule_knowledge, ensure_ascii=False)}
- BDM基线画像: {json.dumps(self.bdm_baseline, ensure_ascii=False)}
- 当前实时上下文: {json.dumps(extra, ensure_ascii=False)}

回答规则:
1. 只回答冲锋赛和业务相关的问题
2. 所有数字务必引用给定的上下文，不要编造
3. 回答使用 Markdown 格式，分条列出
4. 回答结尾附上"仅供参考，最终以当周实际业务为准"
"""
        messages = [
            {"role": "system", "content": system_prompt},
            *self.history[-10:],
            {"role": "user", "content": query}
        ]

        try:
            resp = requests.post(
                self.base_url or "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}",
                         "Content-Type": "application/json"},
                json={"model": "doubao-pro-32k", "messages": messages, "temperature": 0.2},
                timeout=30
            )
            resp.raise_for_status()
            content = resp.json()['choices'][0]['message']['content']
            return self._build_reply(content, type='markdown')
        except Exception as e:
            logger.error(f"[AI Agent] LLM调用失败: {e}，回退规则模式")
            return self._rule_chat(query, extra)
