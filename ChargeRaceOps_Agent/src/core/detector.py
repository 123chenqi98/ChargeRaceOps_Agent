from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
from loguru import logger

from config import Config


class AlertDetector:
    """
    数据预警规则引擎

    四条核心规则：
    - R1: 低完成率预警（总量视角-过去）
    - R2: 增速停滞预警（动能视角-现在）
    - R3: 冲刺不足预警（预测视角-未来）
    - R4: 层级失衡预警（结构视角-内部）
    """

    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.rules_config = self.config.rules
        self._alert_history: Dict[str, List[dict]] = {}

    def detect(self, metrics: List[dict], increments: Dict = None) -> List[dict]:
        """
        执行所有预警规则检测

        Args:
            metrics: 指标数据列表
            increments: 增量数据 {target_id: {increment, hours}}

        Returns:
            Alert事件列表: [{alert_id, rule_id, rule_name, target_id, target_name, level, metric_id, value, threshold, ts}]
        """
        alerts = []

        r1_alerts = self._detect_R1(metrics)
        alerts.extend(r1_alerts)

        r2_alerts = self._detect_R2(metrics, increments or {})
        alerts.extend(r2_alerts)

        r3_alerts = self._detect_R3(metrics, increments or {})
        alerts.extend(r3_alerts)

        r4_alerts = self._detect_R4(metrics)
        alerts.extend(r4_alerts)

        alerts = self._apply_cooldown(alerts)
        alerts = self._deduplicate(alerts)

        if alerts:
            logger.warning(f"[预警检测] 发现 {len(alerts)} 条预警")
            for alert in alerts:
                logger.warning(f"  - [{alert['rule_id']}] {alert['target_name']}/{alert['metric_name']}: {alert['value']:.1f}% < {alert['threshold']}%")
        else:
            logger.info("[预警检测] 未发现异常")

        return alerts

    def _detect_R1(self, metrics: List[dict]) -> List[dict]:
        """
        R1: 低完成率预警
        规则：核心指标完成度 < 60%
        视角：总量视角（过去）
        """
        rule_cfg = self.rules_config.get("R1", {})
        threshold = rule_cfg.get("threshold", 60)
        levels = rule_cfg.get("levels", ["bdm", "cm"])

        alerts = []
        for m in metrics:
            if m["level"] not in levels:
                continue
            value = m.get("value", 0)
            target_value = m.get("target_value", 100)

            if target_value <= 0:
                continue

            completion_rate = (value / target_value) * 100

            if completion_rate < threshold:
                alert = self._make_alert(
                    rule_id="R1",
                    rule_name="低完成率预警",
                    target=m,
                    value=completion_rate,
                    threshold=threshold,
                    extra={"metric_value": value, "metric_target": target_value},
                )
                alerts.append(alert)

        return alerts

    def _detect_R2(self, metrics: List[dict], increments: Dict) -> List[dict]:
        """
        R2: 增速停滞预警
        规则：连续N小时核销增量=0 且完成度<100%
        视角：动能视角（现在）
        """
        rule_cfg = self.rules_config.get("R2", {})
        threshold = rule_cfg.get("threshold", 2)
        peak_threshold = rule_cfg.get("peak_threshold", 1)
        levels = rule_cfg.get("levels", ["bdm"])

        now = datetime.now()
        is_peak_hour = now.hour >= 20

        effective_threshold = peak_threshold if is_peak_hour else threshold

        alerts = []
        for target_id, inc_data in increments.items():
            bdm_metrics = [m for m in metrics if m["target_id"] == target_id and m["level"] in levels]
            if not bdm_metrics:
                continue

            increment = inc_data.get("increment", 0)
            hours = inc_data.get("hours", 2)

            if increment == 0 and hours >= effective_threshold:
                completion_rate = 0
                for m in bdm_metrics:
                    if m["metric_id"] == "double_complete_rate":
                        tv = m.get("target_value", 100)
                        if tv > 0:
                            completion_rate = (m.get("value", 0) / tv) * 100
                        break

                if completion_rate < 100:
                    alert = self._make_alert(
                        rule_id="R2",
                        rule_name="增速停滞预警",
                        target=bdm_metrics[0],
                        value=completion_rate,
                        threshold=effective_threshold,
                        extra={"increment": increment, "stagnant_hours": hours},
                    )
                    alerts.append(alert)

        return alerts

    def _detect_R3(self, metrics: List[dict], increments: Dict) -> List[dict]:
        """
        R3: 冲刺不足预警
        规则：预计到22:00无法完成目标
        视角：预测视角（未来）
        """
        rule_cfg = self.rules_config.get("R3", {})
        threshold_hours = rule_cfg.get("threshold_hours_before_end", 3)
        levels = rule_cfg.get("levels", ["bdm"])

        now = datetime.now()
        end_of_day = now.replace(hour=22, minute=0, second=0, microsecond=0)
        remaining_hours = max(0, (end_of_day - now).total_seconds() / 3600)

        if remaining_hours > threshold_hours:
            return []

        alerts = []
        for m in metrics:
            if m["level"] not in levels:
                continue
            if m["metric_id"] not in ["single_complete_rate", "double_complete_rate", "scan_complete_rate"]:
                continue

            current_value = m.get("value", 0)
            target_value = m.get("target_value", 100)
            gap = max(0, target_value - current_value)

            if target_value <= 0 or gap <= 0:
                continue

            target_id = m["target_id"]
            inc_data = increments.get(target_id, {})
            increment = inc_data.get("increment", 0)
            inc_hours = inc_data.get("hours", 2)

            if inc_hours <= 0 or increment <= 0:
                avg_speed = 0
            else:
                avg_speed = increment / inc_hours

            predicted_value = current_value + avg_speed * remaining_hours
            predicted_gap = max(0, target_value - predicted_value)

            if predicted_gap > 0 and avg_speed > 0:
                alert = self._make_alert(
                    rule_id="R3",
                    rule_name="冲刺不足预警",
                    target=m,
                    value=gap,
                    threshold=predicted_gap,
                    extra={
                        "current_value": current_value,
                        "target_value": target_value,
                        "predicted_value": predicted_value,
                        "remaining_hours": remaining_hours,
                        "avg_speed": avg_speed,
                    },
                )
                alerts.append(alert)

        return alerts

    def _detect_R4(self, metrics: List[dict]) -> List[dict]:
        """
        R4: 层级失衡预警
        规则：同BDM下CM综合达成极差 > 40%
        视角：结构视角（内部）
        """
        rule_cfg = self.rules_config.get("R4", {})
        threshold = rule_cfg.get("threshold", 40)
        levels = rule_cfg.get("levels", ["bdm"])

        cm_metrics = [m for m in metrics if m["level"] == "cm"]

        bdm_cms: Dict[str, List[dict]] = {}
        for m in cm_metrics:
            bdm_id = m.get("bdm_id", m.get("parent_id", ""))
            if bdm_id:
                if bdm_id not in bdm_cms:
                    bdm_cms[bdm_id] = []
                bdm_cms[bdm_id].append(m)

        alerts = []
        for bdm_id, cms in bdm_cms.items():
            comprehensive_values = [
                c["value"] for c in cms
                if c["metric_id"] == "cm_comprehensive"
            ]

            if len(comprehensive_values) >= 2:
                max_val = max(comprehensive_values)
                min_val = min(comprehensive_values)
                gap = max_val - min_val

                if gap > threshold:
                    best_cm = max(cms, key=lambda x: x.get("value", 0))
                    worst_cm = min(cms, key=lambda x: x.get("value", 0))

                    alert = self._make_alert(
                        rule_id="R4",
                        rule_name="层级失衡预警",
                        target=cms[0],
                        value=gap,
                        threshold=threshold,
                        extra={
                            "bdm_id": bdm_id,
                            "max_cm": best_cm.get("target_name", ""),
                            "max_value": max_val,
                            "min_cm": worst_cm.get("target_name", ""),
                            "min_value": min_val,
                            "cm_count": len(comprehensive_values),
                        },
                    )
                    alerts.append(alert)

        return alerts

    def _make_alert(
        self,
        rule_id: str,
        rule_name: str,
        target: dict,
        value: float,
        threshold: float,
        extra: dict = None,
    ) -> dict:
        return {
            "alert_id": str(uuid.uuid4())[:8],
            "rule_id": rule_id,
            "rule_name": rule_name,
            "target_id": target.get("target_id", ""),
            "target_name": target.get("target_name", ""),
            "level": target.get("level", ""),
            "metric_id": target.get("metric_id", ""),
            "metric_name": target.get("metric_name", ""),
            "value": round(value, 2),
            "threshold": threshold,
            "extra": extra or {},
            "ts": datetime.now().isoformat(),
            "status": "open",
        }

    def _apply_cooldown(self, alerts: List[dict]) -> List[dict]:
        """
        应用防抖策略：同一对象同一规则在冷却期内不重复触发
        """
        now = datetime.now()
        valid_alerts = []

        for alert in alerts:
            key = f"{alert['target_id']}_{alert['rule_id']}"
            history = self._alert_history.get(key, [])

            if history:
                last_alert = history[-1]
                last_ts = datetime.fromisoformat(last_alert["ts"])
                cooldown = self._get_cooldown(alert["rule_id"])

                if (now - last_ts).total_seconds() < cooldown:
                    logger.debug(
                        f"[防抖] 跳过 {alert['target_name']}/{alert['rule_id']}"
                        f"（冷却中，还剩{int(cooldown - (now - last_ts).total_seconds())}秒）"
                    )
                    continue

            valid_alerts.append(alert)

        return valid_alerts

    def _get_cooldown(self, rule_id: str) -> int:
        rule_cfg = self.rules_config.get(rule_id, {})
        return rule_cfg.get("cooldown_minutes", 120) * 60

    def _deduplicate(self, alerts: List[dict]) -> List[dict]:
        seen = set()
        result = []
        for alert in alerts:
            key = f"{alert['target_id']}_{alert['rule_id']}_{alert['metric_id']}"
            if key not in seen:
                seen.add(key)
                result.append(alert)

        for alert in result:
            key = f"{alert['target_id']}_{alert['rule_id']}"
            if key not in self._alert_history:
                self._alert_history[key] = []
            self._alert_history[key].append(alert)

        return result

    def get_rules_status(self) -> Dict:
        """获取规则状态统计"""
        stats = {}
        for rule_id in self.rules_config:
            history_count = sum(
                len(h) for k, h in self._alert_history.items()
                if k.endswith(f"_{rule_id}")
            )
            stats[rule_id] = {
                "name": self.rules_config[rule_id].get("name", ""),
                "total_alerts": history_count,
                "config": self.rules_config[rule_id],
            }
        return stats
