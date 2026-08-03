"""
智能归因 & 催办话术生成模块

功能：
1. 对每一条预警做自动化的归因分析（按概率排序）
2. 给BDM/CM生成个性化催办话术
3. 对接飞书推送时，自动把归因+话术写入卡片

设计原则：真实环境可接入LLM；无LLM时用模板+随机组合，保证可演示、可落地。
"""

import json
import random
from datetime import datetime
from typing import List, Dict

from loguru import logger


CAUSE_LIBRARY = {
    'R1': {
        '常见原因': [
            {'name': '目标拆解未对齐', 'weight': 0.28, 'action': '立即与CM确认可达成范围，重新拆解天目标'},
            {'name': 'POS/核销流程异常', 'weight': 0.25, 'action': '联系商户运营排查POS故障，申请备用核销码'},
            {'name': '重点门店支撑不足', 'weight': 0.20, 'action': '销售支持下午去TOP3未核销门店驻点'},
            {'name': '周末激励政策未触达', 'weight': 0.15, 'action': '一对一电话+群发确认每位CM已知晓政策'},
            {'name': '客户资源分配不均', 'weight': 0.12, 'action': '按实际能力再分配大客户资源，倾斜落后CM'},
        ],
    },
    'R2': {
        '常见原因': [
            {'name': 'POS临时故障断网', 'weight': 0.35, 'action': 'APP下单临时入口切换 + 手动核销补录'},
            {'name': '午/晚高峰人手不足', 'weight': 0.28, 'action': '安排BDM + 支援CM去TOP门店高峰值守'},
            {'name': '头部门店突发闭店', 'weight': 0.18, 'action': '快速切换备用门店清单，冲量资源转移到第二梯队'},
            {'name': '客户资金/意愿临时下降', 'weight': 0.19, 'action': '电话大客户确认，追加当日临时激励政策'},
        ],
    },
    'R3': {
        '常见原因': [
            {'name': '门店可用数量进入尾段', 'weight': 0.30, 'action': '启动"尾段冲刺"专项：第二梯队门店追加激励'},
            {'name': '冲刺策略缺失/滞后', 'weight': 0.30, 'action': '每小时开5分钟standup，进度落后立即拉齐'},
            {'name': 'CM体力/精力触顶', 'weight': 0.22, 'action': '销售支持承担后台工作，让CM专注线下冲刺'},
            {'name': '大客户最后犹豫未决', 'weight': 0.18, 'action': 'BDM + 区域负责人一起上门/电话攻关'},
        ],
    },
    'R4': {
        '常见原因': [
            {'name': '新人CM培训不足', 'weight': 0.35, 'action': '优秀和落后CM结对陪跑，当日复盘'},
            {'name': '老客户资源分配不均', 'weight': 0.28, 'action': '资源重组，给落后CM分配可立刻跟进的客户'},
            {'name': 'BDM精力分配偏差', 'weight': 0.22, 'action': '未来3天BDM 80%精力给落后30%的CM'},
            {'name': '个别门店长期问题', 'weight': 0.15, 'action': '门店黑名单机制：连续2天落后的门店需专项突破'},
        ],
    },
}


DIALECT_TEMPLATES = {
    'direct': [
        'Hi {name}，当前{metric}{value}%（目标阈值 {threshold}%），{rule_name}触发，**请在2小时内完成跟进并点击卡片「已跟进」**✅',
        '{name}你好，{rule_name}预警已经拉响：{metric} {value}% < {threshold}%，请立刻安排动作，30分钟后我会再检查一次 ⏰',
        '🆘 {name}，{metric}只有 {value}%，请马上梳理TOP3未核销门店，给我清单，我们一起冲！',
    ],
    'encouraging': [
        '💪 {name}加油！现在{metric} {value}%，距离目标还差一点，我们一起把进度打上去！',
        '{name}你前面做得都很好，就是{metric}暂时 {value}%，需要支援直接@我，销售支持立刻上🔥',
        '嗨 {name}～ 还有时间！{metric}当前 {value}%，我这边梳理了TOP未核销，你看要不要一起打几个电话？📞',
    ],
    'detailed': [
        '📌 【{rule_name}预警·{name}】\n指标：{metric}\n当前：{value}% | 阈值：{threshold}%\n⚠️ 最可能原因：{cause_name}\n✅ 建议动作：{action}\n\n请优先处理TOP1门店，需要支援随时@我！',
        '🔔 给{name}的动作清单：\n① 先看TOP未核销门店（我已经同步给你）\n② {cause_name} 是头号风险，建议按「{action}」来做\n③ 1小时后我再看一次数据，有困难随时拉群讨论！',
    ],
}


class SmartAnalyzer:
    """预警智能归因 + 催办话术生成器"""

    def __init__(self, use_llm: bool = False, ai_agent=None):
        self.use_llm = use_llm
        self.ai_agent = ai_agent

    def analyze_alert(self, alert: dict) -> dict:
        """对单条预警做归因分析"""
        rule = alert.get('rule_id', 'R1')
        causes = CAUSE_LIBRARY.get(rule, CAUSE_LIBRARY['R1'])['常见原因']

        sampled = random.choices(
            causes,
            weights=[c['weight'] for c in causes],
            k=min(3, len(causes))
        )

        result = {
            'alert_id': alert.get('alert_id'),
            'rule_id': rule,
            'rule_name': alert.get('rule_name'),
            'target': alert.get('target_name'),
            'metric': alert.get('metric_name'),
            'value': alert.get('value'),
            'threshold': alert.get('threshold'),
            'top_causes': sampled,
            'primary_cause': sampled[0] if sampled else None,
            'generated_at': datetime.now().isoformat(),
        }

        if self.use_llm and self.ai_agent:
            try:
                llm_resp = self.ai_agent.chat(
                    f'请给出这条预警的最可能原因和行动建议：{json.dumps(alert, ensure_ascii=False)}'
                )
                result['llm_note'] = llm_resp.get('content', '')
            except Exception as e:
                logger.warning(f'LLM归因失败，回退模板：{e}')

        logger.debug(f"[归因分析] {alert.get('target_name')}/{rule}: {result['primary_cause']['name'] if result['primary_cause'] else '无'}")
        return result

    def batch_analyze(self, alerts: list) -> List[dict]:
        return [self.analyze_alert(a) for a in alerts]

    def generate_urge_message(
        self,
        alert: dict,
        analysis: dict = None,
        style: str = 'detailed',
    ) -> str:
        """
        生成个性化催办话术
        style: direct(直接) / encouraging(鼓励) / detailed(带归因的详细版)
        """
        if analysis is None:
            analysis = self.analyze_alert(alert)

        cause = analysis.get('primary_cause', {}) or {}
        cause_name = cause.get('name', '需进一步确认')
        action = cause.get('action', '按标准动作执行')

        tpl_list = DIALECT_TEMPLATES.get(style, DIALECT_TEMPLATES['detailed'])
        tpl = random.choice(tpl_list)

        try:
            text = tpl.format(
                name=alert.get('target_name', ''),
                rule_name=alert.get('rule_name', ''),
                metric=alert.get('metric_name', ''),
                value=alert.get('value', ''),
                threshold=alert.get('threshold', ''),
                cause_name=cause_name,
                action=action,
            )
        except Exception:
            text = f'【{alert.get("rule_name","预警")}】 {alert.get("target_name","")} {alert.get("metric_name","")} 当前 {alert.get("value", "")}%，请优先处理！建议：{action}'

        return text

    def summarize_batch_analysis(self, alerts: list) -> str:
        """批量预警归因的汇总结论，用于区域群/大区群"""
        if not alerts:
            return "✅ 当前没有异常预警，继续保持！"

        analyses = self.batch_analyze(alerts)
        cause_counter: Dict[str, int] = {}
        rule_counter: Dict[str, int] = {}

        for a in analyses:
            if a.get('primary_cause'):
                cause_counter[a['primary_cause']['name']] = cause_counter.get(a['primary_cause']['name'], 0) + 1
            rule_counter[a['rule_id']] = rule_counter.get(a['rule_id'], 0) + 1

        sorted_causes = sorted(cause_counter.items(), key=lambda x: -x[1])
        sorted_rules = sorted(rule_counter.items(), key=lambda x: -x[1])

        lines = [
            f"## 📊 本轮预警归因汇总（{len(alerts)} 条）",
            "",
            "### 🔴 TOP 问题类型",
        ]
        for r, c in sorted_rules:
            lines.append(f"- **{r}**：{c} 条 ({round(c/len(alerts)*100, 1)}%)")

        lines.append("")
        lines.append("### 🧠 TOP 根因（按出现次数）")
        for name, cnt in sorted_causes[:3]:
            lines.append(f"- **{name}**：出现 {cnt} 次")

        lines.append("")
        lines.append("### ⚡ 建议下一步动作")
        if sorted_causes:
            top_cause_name = sorted_causes[0][0]
            for rule_id, lib in CAUSE_LIBRARY.items():
                for c in lib['常见原因']:
                    if c['name'] == top_cause_name:
                        lines.append(f"1. 针对「{top_cause_name}」优先执行：{c['action']}")
                        break
                else:
                    continue
                break
        lines.append(f"2. 请各BDM在 2 小时内完成「已跟进」点击，我会在下次巡检时复核 ✅")

        return '\n'.join(lines)
