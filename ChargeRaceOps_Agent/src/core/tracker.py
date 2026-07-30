from datetime import datetime
from typing import Dict, List, Optional
import requests
from loguru import logger

from config import Config


class StateTracker:
    """
    预警状态追踪模块

    维护 open → acknowledged → snoozed → expired 三态状态机
    数据存储在飞书多维表格中，支持事后复盘
    """

    STATES = {
        "open": "待跟进",
        "acknowledged": "已跟进",
        "snoozed": "暂缓",
        "expired": "已过期",
    }

    def __init__(self, config: Config = None):
        self.config = config or Config()
        self._states: Dict[str, dict] = {}
        self._bitable_base = "https://open.feishu.cn/open-apis/bitable/v1"
        self._app_token = self.config.state_store.get("bitable_app_token", "")
        self._table_id = self.config.state_store.get("bitable_table_id", "")

    def record_alert(self, alert: dict) -> dict:
        """
        记录新预警到状态机

        Returns:
            记录结果
        """
        alert_id = alert["alert_id"]
        record = {
            "alert_id": alert_id,
            "rule_id": alert["rule_id"],
            "rule_name": alert["rule_name"],
            "target_id": alert["target_id"],
            "target_name": alert["target_name"],
            "level": alert["level"],
            "metric_id": alert["metric_id"],
            "value": alert["value"],
            "threshold": alert["threshold"],
            "status": "open",
            "created_at": alert.get("ts", datetime.now().isoformat()),
            "acknowledged_at": None,
            "acknowledged_by": None,
            "extra": alert.get("extra", {}),
        }

        self._states[alert_id] = record

        self._save_to_bitable(record)

        logger.info(f"[状态追踪] 记录预警: {alert_id} ({alert['rule_name']})")
        return record

    def acknowledge_alert(self, alert_id: str, acknowledger: str) -> dict:
        """
        标记预警为已跟进

        Args:
            alert_id: 预警ID
            acknowledger: 跟进人

        Returns:
            更新后的记录
        """
        record = self._states.get(alert_id)
        if not record:
            logger.warning(f"[状态追踪] 未找到预警: {alert_id}")
            return {}

        record["status"] = "acknowledged"
        record["acknowledged_at"] = datetime.now().isoformat()
        record["acknowledged_by"] = acknowledger

        self._update_bitable(alert_id, record)

        logger.info(f"[状态追踪] 预警已跟进: {alert_id} by {acknowledger}")
        return record

    def snooze_alert(self, alert_id: str, minutes: int = 30) -> dict:
        """
        暂缓预警，N分钟后重新触发

        Args:
            alert_id: 预警ID
            minutes: 暂缓分钟数

        Returns:
            更新后的记录
        """
        record = self._states.get(alert_id)
        if not record:
            return {}

        record["status"] = "snoozed"
        record["snooze_until"] = datetime.now().timestamp() + minutes * 60

        self._update_bitable(alert_id, record)

        logger.info(f"[状态追踪] 预警暂缓: {alert_id} for {minutes}min")
        return record

    def expire_alerts(self, before_ts: str = None) -> int:
        """
        过期处理：将长时间未跟进的预警标记为expired

        Returns:
            过期处理的预警数量
        """
        if before_ts is None:
            from datetime import timedelta
            before_ts = (datetime.now() - timedelta(hours=4)).isoformat()

        expired_count = 0
        for alert_id, record in self._states.items():
            if record["status"] == "open" and record["created_at"] < before_ts:
                record["status"] = "expired"
                self._update_bitable(alert_id, record)
                expired_count += 1

        if expired_count > 0:
            logger.info(f"[状态追踪] 过期处理: {expired_count} 条预警标记为expired")

        return expired_count

    def get_open_alerts(self) -> List[dict]:
        """获取所有待跟进的预警"""
        return [
            r for r in self._states.values()
            if r["status"] == "open"
        ]

    def get_alert_stats(self) -> dict:
        """获取预警统计数据"""
        stats = {"total": 0, "open": 0, "acknowledged": 0, "snoozed": 0, "expired": 0}
        for record in self._states.values():
            stats["total"] += 1
            status = record["status"]
            if status in stats:
                stats[status] += 1
        return stats

    def get_recap_data(self, start_ts: str = None, end_ts: str = None) -> dict:
        """
        获取复盘数据

        Returns:
            {
                "total_alerts": N,
                "open_count": N,
                "acknowledged_count": N,
                "expired_count": N,
                "acknowledge_rate": percentage,
                "by_rule": {rule_id: count},
                "by_target": {target_name: count},
            }
        """
        records = self._states.values()

        if start_ts:
            records = [r for r in records if r["created_at"] >= start_ts]
        if end_ts:
            records = [r for r in records if r["created_at"] <= end_ts]

        total = len(records)
        open_count = sum(1 for r in records if r["status"] == "open")
        ack_count = sum(1 for r in records if r["status"] == "acknowledged")
        expired_count = sum(1 for r in records if r["status"] == "expired")
        snoozed_count = sum(1 for r in records if r["status"] == "snoozed")

        by_rule: Dict[str, int] = {}
        by_target: Dict[str, int] = {}
        for r in records:
            by_rule[r["rule_id"]] = by_rule.get(r["rule_id"], 0) + 1
            by_target[r["target_name"]] = by_target.get(r["target_name"], 0) + 1

        return {
            "total_alerts": total,
            "open_count": open_count,
            "acknowledged_count": ack_count,
            "expired_count": expired_count,
            "snoozed_count": snoozed_count,
            "acknowledge_rate": round(ack_count / max(total, 1) * 100, 1),
            "by_rule": by_rule,
            "by_target": by_target,
            "generated_at": datetime.now().isoformat(),
        }

    def _save_to_bitable(self, record: dict):
        """保存记录到飞书多维表格"""
        if not self._app_token or not self._table_id:
            logger.debug("[状态追踪] 多维表格未配置，跳过持久化")
            return

        url = f"{self._bitable_base}/apps/{self._app_token}/tables/{self._table_id}/records"
        payload = {
            "fields": {
                "预警ID": record["alert_id"],
                "规则ID": record["rule_id"],
                "规则名称": record["rule_name"],
                "目标ID": record["target_id"],
                "目标名称": record["target_name"],
                "层级": record["level"],
                "指标ID": record["metric_id"],
                "数值": record["value"],
                "阈值": record["threshold"],
                "状态": self.STATES.get(record["status"], record["status"]),
                "创建时间": record["created_at"],
            }
        }

        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.json().get("code") == 0:
                logger.debug(f"[状态追踪] 已保存到多维表格: {record['alert_id']}")
        except Exception as e:
            logger.warning(f"[状态追踪] 保存多维表格失败: {e}")

    def _update_bitable(self, alert_id: str, record: dict):
        """更新多维表格中的记录"""
        if not self._app_token or not self._table_id:
            return

        url = f"{self._bitable_base}/apps/{self._app_token}/tables/{self._table_id}/records"
        payload = {
            "filter": {
                "conjunction": "and",
                "conditions": [
                    {
                        "field_name": "预警ID",
                        "operator": "is",
                        "value": [alert_id],
                    }
                ],
            },
            "fields": {
                "状态": self.STATES.get(record["status"], record["status"]),
                "跟进时间": record.get("acknowledged_at", ""),
                "跟进人": record.get("acknowledged_by", ""),
            },
        }

        try:
            requests.patch(url, json=payload, timeout=10)
        except Exception:
            pass
