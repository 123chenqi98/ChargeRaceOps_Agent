from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger

from config import Config


class RecapGenerator:
    """
    复盘报告生成模块

    冲锋赛后自动生成结构化数据复盘：
    - 预警覆盖率
    - 预警跟进率
    - 挽回目标额（估算）
    - 规则效果评估
    - 异常BDM排名
    """

    def __init__(self, config: Config = None):
        self.config = config or Config()

    def generate(
        self,
        recap_data: dict,
        campaign_name: str = "",
        save_path: str = None,
    ) -> str:
        """
        生成结构化复盘报告

        Args:
            recap_data: 状态追踪器提供的复盘数据
            campaign_name: 冲锋赛名称
            save_path: 保存路径

        Returns:
            Markdown格式的复盘报告
        """
        now = datetime.now()
        md_lines = []

        md_lines.append(f"# {campaign_name} 复盘报告")
        md_lines.append(f"")
        md_lines.append(f"> 生成时间：{now.strftime('%Y-%m-%d %H:%M:%S')}")
        md_lines.append(f"> 数据来源：预警状态追踪系统")
        md_lines.append(f"")

        md_lines.append("## 📊 核心指标概览")
        md_lines.append(f"")

        total = recap_data.get("total_alerts", 0)
        open_count = recap_data.get("open_count", 0)
        ack_count = recap_data.get("acknowledged_count", 0)
        expired_count = recap_data.get("expired_count", 0)
        acknowledge_rate = recap_data.get("acknowledge_rate", 0)

        md_lines.append(f"| 指标 | 数值 | 说明 |")
        md_lines.append(f"|------|------|------|")
        md_lines.append(f"| **预警总数** | {total} 条 | 冲锋期间触发的所有预警 |")
        md_lines.append(f"| **已跟进** | {ack_count} 条 | 标记为已处理的预警 |")
        md_lines.append(f"| **待跟进** | {open_count} 条 | 仍在等待处理的预警 |")
        md_lines.append(f"| **已过期** | {expired_count} 条 | 超过时效未跟进的预警 |")
        md_lines.append(f"| **跟进率** | {acknowledge_rate}% | 已跟进 / 总数 |")
        md_lines.append(f"")

        md_lines.append("## 📈 预警规则效果分析")
        md_lines.append(f"")

        by_rule = recap_data.get("by_rule", {})
        md_lines.append(f"| 规则ID | 规则名称 | 触发次数 | 占比 |")
        md_lines.append(f"|--------|---------|---------|------|")

        rule_names = {
            "R1": "低完成率预警",
            "R2": "增速停滞预警",
            "R3": "冲刺不足预警",
            "R4": "层级失衡预警",
        }

        for rule_id, count in sorted(by_rule.items()):
            name = rule_names.get(rule_id, rule_id)
            percentage = round(count / max(total, 1) * 100, 1)
            md_lines.append(f"| {rule_id} | {name} | {count} | {percentage}% |")

        md_lines.append(f"")

        md_lines.append("## 👤 异常对象排名")
        md_lines.append(f"")

        by_target = recap_data.get("by_target", {})
        sorted_targets = sorted(by_target.items(), key=lambda x: -x[1])

        md_lines.append(f"| 排名 | 目标名称 | 预警次数 |")
        md_lines.append(f"|------|---------|---------|")
        for rank, (target, count) in enumerate(sorted_targets[:10], 1):
            md_lines.append(f"| {rank} | {target} | {count} |")

        md_lines.append(f"")

        md_lines.append("## 💡 复盘建议")
        md_lines.append(f"")

        suggestions = self._generate_suggestions(recap_data)
        for suggestion in suggestions:
            md_lines.append(f"- {suggestion}")

        md_lines.append(f"")
        md_lines.append("---")
        md_lines.append(f"*报告由数据驱动复盘系统自动生成*")

        report_content = "\n".join(md_lines)

        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(report_content)
            logger.info(f"[复盘] 报告已保存: {save_path}")

        return report_content

    def _generate_suggestions(self, recap_data: dict) -> List[str]:
        """基于数据生成复盘建议"""
        suggestions = []

        acknowledge_rate = recap_data.get("acknowledge_rate", 0)
        if acknowledge_rate < 70:
            suggestions.append(
                f"⚠️ 跟进率偏低（{acknowledge_rate}%），建议在冲锋日设置专门的预警响应窗口"
            )
        elif acknowledge_rate < 85:
            suggestions.append(
                f"⚡ 跟进率待提升（{acknowledge_rate}%），可优化预警推送时机和内容颗粒度"
            )
        else:
            suggestions.append(f"✅ 跟进率良好（{acknowledge_rate}%），保持现有节奏")

        total = recap_data.get("total_alerts", 0)
        if total > 100:
            suggestions.append(
                f"📊 预警量较大（{total}条），建议分析是否存在规则过于敏感的情况，考虑调整阈值"
            )
        elif total < 20:
            suggestions.append(
                f"🔍 预警量偏少（{total}条），可能存在规则过于严格或数据异常的情况，建议排查"
            )

        expired = recap_data.get("expired_count", 0)
        if expired > 0:
            expired_rate = round(expired / max(total, 1) * 100, 1)
            suggestions.append(
                f"⏰ 存在 {expired} 条过期预警（占比 {expired_rate}%），建议优化预警时效和跟进提醒机制"
            )

        by_rule = recap_data.get("by_rule", {})
        r1_count = by_rule.get("R1", 0)
        r2_count = by_rule.get("R2", 0)

        if r1_count > r2_count * 2:
            suggestions.append(
                f"📈 低完成率预警（{r1_count}条）远多于增速停滞预警（{r2_count}条），"
                f"说明BDM存在长期落后问题，建议加强日常辅导"
            )
        elif r2_count > r1_count * 2:
            suggestions.append(
                f"⚡ 增速停滞预警（{r2_count}条）远多于低完成率预警（{r1_count}条），"
                f"说明BDM可能临时遇到障碍（如POS故障、头部门店问题），建议排查具体原因"
            )

        if not suggestions:
            suggestions.append("🔄 建议对照上一轮冲锋赛数据，分析规则阈值的合理性")
            suggestions.append("📝 建议收集BDM反馈，优化预警内容的可操作性")

        return suggestions


def print_recap_summary(recap_data: dict):
    """在终端打印复盘摘要"""
    print("\n" + "=" * 60)
    print("📊 冲锋赛复盘摘要")
    print("=" * 60)
    print(f"  预警总数: {recap_data.get('total_alerts', 0)}")
    print(f"  已跟进:   {recap_data.get('acknowledged_count', 0)}")
    print(f"  待跟进:   {recap_data.get('open_count', 0)}")
    print(f"  跟进率:   {recap_data.get('acknowledge_rate', 0)}%")
    print("-" * 60)
    print("  按规则分布:")
    for rule_id, count in sorted(recap_data.get("by_rule", {}).items()):
        print(f"    {rule_id}: {count} 条")
    print("-" * 60)
    print("  TOP 5 异常对象:")
    sorted_targets = sorted(
        recap_data.get("by_target", {}).items(),
        key=lambda x: -x[1]
    )[:5]
    for target, count in sorted_targets:
        print(f"    {target}: {count} 条")
    print("=" * 60)
