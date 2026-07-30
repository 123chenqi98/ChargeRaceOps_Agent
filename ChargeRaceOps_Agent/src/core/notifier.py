import json
from typing import Dict, List, Optional
import requests
from loguru import logger

from config import Config


class FeishuNotifier:
    """
    飞书消息推送模块

    按四层结构（region/city/bdm/cm）差异化推送预警卡片
    """

    RULE_COLORS = {
        "R1": "red",
        "R2": "orange",
        "R3": "blue",
        "R4": "purple",
    }

    RULE_ICONS = {
        "R1": "⚠️",
        "R2": "⏸️",
        "R3": "🏃",
        "R4": "📊",
    }

    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.base_url = "https://open.feishu.cn/open-apis"
        self.app_id = self.config.get_feishu_app_id()
        self.app_secret = self.config.get_feishu_app_secret()
        self._tenant_token = None

    def _get_tenant_token(self) -> str:
        if self._tenant_token:
            return self._tenant_token

        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }

        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            self._tenant_token = resp.json().get("tenant_access_token", "")
            return self._tenant_token
        except Exception as e:
            logger.error(f"[飞书] 获取tenant_token失败: {e}")
            return ""

    def send_alerts(self, alerts: List[dict], identity_map: Dict = None) -> List[dict]:
        """
        按层级路由推送预警

        Args:
            alerts: 预警列表
            identity_map: 身份映射 {bdm_name: {open_id, email}}

        Returns:
            发送结果列表
        """
        results = []
        identity_map = identity_map or {}

        grouped_alerts = self._group_by_level(alerts)

        for level, level_alerts in grouped_alerts.items():
            send_func = getattr(self, f"_send_{level}_alerts", None)
            if send_func:
                batch_results = send_func(level_alerts, identity_map)
                results.extend(batch_results)

        logger.info(f"[飞书] 推送完成: {len(results)} 条预警已发送")
        return results

    def _group_by_level(self, alerts: List[dict]) -> Dict[str, List[dict]]:
        groups = {"region": [], "city": [], "bdm": [], "cm": []}
        for alert in alerts:
            level = alert.get("level", "")
            if level == "city":
                groups["city"].append(alert)
            elif level == "bdm":
                groups["bdm"].append(alert)
            elif level == "cm":
                groups["cm"].append(alert)
            else:
                groups["region"].append(alert)
        return {k: v for k, v in groups.items() if v}

    def _send_region_alerts(self, alerts: List[dict], identity_map: Dict) -> List[dict]:
        """三级区域群推送：汇总排名"""
        if not alerts:
            return []

        notif_config = self.config.notification.get("layers", {}).get("region", {})
        if not notif_config.get("enabled", False):
            return []

        chat_id = notif_config.get("chat_id", "")
        if not chat_id:
            logger.warning("[飞书] region chat_id未配置，跳过推送")
            return []

        summary = self._build_region_summary(alerts)
        card = self._build_card(summary, "region")

        return self._send_card(chat_id, card, "chat")

    def _send_city_alerts(self, alerts: List[dict], identity_map: Dict) -> List[dict]:
        """四级城市区域群推送：本区域明细"""
        if not alerts:
            return []

        notif_config = self.config.notification.get("layers", {}).get("city", {})
        if not notif_config.get("enabled", False):
            return []

        chat_ids_str = notif_config.get("chat_ids", "")
        chat_ids = [cid.strip() for cid in chat_ids_str.split(",") if cid.strip()]

        results = []
        city_groups: Dict[str, List[dict]] = {}

        for alert in alerts:
            city = alert.get("extra", {}).get("city", alert.get("target_name", "未知城市"))
            if city not in city_groups:
                city_groups[city] = []
            city_groups[city].append(alert)

        for chat_id in chat_ids:
            for city, city_alerts in city_groups.items():
                card = self._build_card(
                    self._build_city_detail(city_alerts, city), "city"
                )
                results.extend(self._send_card(chat_id, card, "chat"))

        return results

    def _send_bdm_alerts(self, alerts: List[dict], identity_map: Dict) -> List[dict]:
        """BDM私聊推送：个人指标"""
        if not alerts:
            return []

        notif_config = self.config.notification.get("layers", {}).get("bdm", {})
        if not notif_config.get("enabled", False):
            return []

        results = []
        bdm_groups: Dict[str, List[dict]] = {}

        for alert in alerts:
            bdm_id = alert.get("target_id", "")
            if bdm_id not in bdm_groups:
                bdm_groups[bdm_id] = []
            bdm_groups[bdm_id].append(alert)

        for bdm_id, bdm_alerts in bdm_groups.items():
            bdm_name = bdm_alerts[0].get("target_name", "")
            open_id = identity_map.get(bdm_name, {}).get("open_id", "")

            if not open_id:
                logger.warning(f"[飞书] 未找到 {bdm_name} 的open_id，跳过私聊推送")
                continue

            card = self._build_card(
                self._build_bdm_detail(bdm_alerts), "bdm"
            )
            results.extend(self._send_card(open_id, card, "open_id"))

        return results

    def _send_cm_alerts(self, alerts: List[dict], identity_map: Dict) -> List[dict]:
        """CM私聊推送：单店详情"""
        if not alerts:
            return []

        notif_config = self.config.notification.get("layers", {}).get("cm", {})
        if not notif_config.get("enabled", False):
            return []

        results = []
        cm_groups: Dict[str, List[dict]] = {}

        for alert in alerts:
            cm_id = alert.get("target_id", "")
            if cm_id not in cm_groups:
                cm_groups[cm_id] = []
            cm_groups[cm_id].append(alert)

        for cm_id, cm_alerts in cm_groups.items():
            cm_name = cm_alerts[0].get("target_name", "")
            open_id = identity_map.get(cm_name, {}).get("open_id", "")

            if not open_id:
                logger.warning(f"[飞书] 未找到 {cm_name} 的open_id，跳过私聊推送")
                continue

            card = self._build_card(
                self._build_cm_detail(cm_alerts), "cm"
            )
            results.extend(self._send_card(open_id, card, "open_id"))

        return results

    def _build_region_summary(self, alerts: List[dict]) -> dict:
        city_stats: Dict[str, int] = {}
        bdm_stats: Dict[str, int] = {}

        for alert in alerts:
            city = alert.get("extra", {}).get("city", "未知")
            city_stats[city] = city_stats.get(city, 0) + 1
            bdm = alert.get("target_name", "")
            bdm_stats[bdm] = bdm_stats.get(bdm, 0) + 1

        sorted_cities = sorted(city_stats.items(), key=lambda x: -x[1])[:5]
        sorted_bdms = sorted(bdm_stats.items(), key=lambda x: -x[1])[:5]

        content_lines = [
            f"**📈 区域预警汇总**",
            f"共发现 **{len(alerts)}** 条预警",
            f"",
            f"**🔴 Top 5 异常城市区域：**",
        ]
        for city, count in sorted_cities:
            content_lines.append(f"  {city}: {count} 条预警")

        content_lines.append(f"")
        content_lines.append(f"**👤 Top 5 异常BDM：**")
        for bdm, count in sorted_bdms:
            content_lines.append(f"  {bdm}: {count} 条预警")

        return {"title": "🔔 区域预警汇总", "content": "\n".join(content_lines)}

    def _build_city_detail(self, alerts: List[dict], city: str) -> dict:
        content_lines = [
            f"**🏙️ {city} - 预警详情**",
            f"共发现 **{len(alerts)}** 条预警",
            f"",
        ]

        bdm_groups: Dict[str, List[dict]] = {}
        for alert in alerts:
            bdm = alert.get("target_name", "未知")
            if bdm not in bdm_groups:
                bdm_groups[bdm] = []
            bdm_groups[bdm].append(alert)

        content_lines.append("**⚠️ 异常BDM列表：**")
        for bdm, bdm_alerts in bdm_groups.items():
            for alert in bdm_alerts:
                rule_icon = self.RULE_ICONS.get(alert["rule_id"], "📌")
                content_lines.append(
                    f"  {rule_icon} **{bdm}** - {alert['metric_name']}: {alert['value']:.1f}%"
                    f"（阈值 {alert['threshold']}%）"
                )

        return {"title": f"🏙️ {city} 预警详情", "content": "\n".join(content_lines)}

    def _build_bdm_detail(self, alerts: List[dict]) -> dict:
        bdm_name = alerts[0].get("target_name", "BDM")
        content_lines = [
            f"**👤 {bdm_name} - 个人预警**",
            f"",
        ]

        for alert in alerts:
            rule_icon = self.RULE_ICONS.get(alert["rule_id"], "📌")
            rule_name = alert["rule_name"]
            extra = alert.get("extra", {})

            if alert["rule_id"] == "R1":
                content_lines.append(
                    f"{rule_icon} **{rule_name}**：{alert['metric_name']} {alert['value']:.1f}%"
                    f"，距目标缺口 **{extra.get('metric_target', 0) - extra.get('metric_value', 0):.0f}**"
                )
            elif alert["rule_id"] == "R2":
                content_lines.append(
                    f"{rule_icon} **{rule_name}**：连续 {alert['threshold']} 小时零增长"
                    f"，当前完成度 {alert['value']:.1f}%"
                )
            elif alert["rule_id"] == "R3":
                content_lines.append(
                    f"{rule_icon} **{rule_name}**：预计 {extra.get('remaining_hours', 0):.0f} 小时后"
                    f"无法完成目标，缺口 {alert['value']:.0f}"
                )
            elif alert["rule_id"] == "R4":
                content_lines.append(
                    f"{rule_icon} **{rule_name}**：CM间极差 {alert['value']:.1f}%"
                )

        content_lines.append(f"")
        content_lines.append(f"💡 **建议动作**：")
        content_lines.append(f"  1. 查看详细数据并跟进")
        content_lines.append(f"  2. 如需暂缓，点击下方按钮")

        return {"title": f"🔔 {bdm_name} 预警", "content": "\n".join(content_lines)}

    def _build_cm_detail(self, alerts: List[dict]) -> dict:
        cm_name = alerts[0].get("target_name", "CM")
        content_lines = [
            f"**🏪 {cm_name} - 单店预警**",
            f"",
        ]

        for alert in alerts:
            rule_icon = self.RULE_ICONS.get(alert["rule_id"], "📌")
            content_lines.append(
                f"{rule_icon} **{alert['rule_name']}**：{alert['metric_name']} {alert['value']:.1f}%"
            )

        content_lines.append(f"")
        content_lines.append(f"📊 同组均值对比：低于组内平均水平")

        return {"title": f"🔔 {cm_name} 预警", "content": "\n".join(content_lines)}

    def _build_card(self, content: dict, level: str) -> dict:
        """构建飞书Interactive Card"""
        template = {
            "region": "blue",
            "city": "green",
            "bdm": "red",
            "cm": "orange",
        }
        color = template.get(level, "blue")

        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": color,
                "title": {
                    "tag": "plain_text",
                    "content": content.get("title", "预警通知"),
                },
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": content.get("content", ""),
                    },
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "✅ 标记已跟进",
                            },
                            "type": "primary",
                            "value": {
                                "action": "acknowledge",
                                "alerts": [a["alert_id"] for a in content.get("_alerts", [])],
                            },
                        },
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "💤 30分钟后再提醒",
                            },
                            "type": "default",
                            "value": {
                                "action": "snooze",
                                "minutes": 30,
                            },
                        },
                    ],
                },
            ],
        }

    def _send_card(self, receive_id: str, card: dict, receive_type: str = "chat") -> List[dict]:
        """发送卡片消息到飞书"""
        token = self._get_tenant_token()
        if not token:
            logger.error("[飞书] 无有效token，跳过发送")
            return []

        url = f"{self.base_url}/im/v1/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        params = {"receive_id_type": receive_type}
        payload = {
            "receive_id": receive_id,
            "msg_type": "interactive",
            "content": json.dumps(card),
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            result = resp.json()

            if result.get("code") == 0:
                message_id = result.get("data", {}).get("message_id", "")
                logger.info(f"[飞书] 卡片发送成功: {receive_id} -> {message_id}")
                return [{"receive_id": receive_id, "message_id": message_id, "status": "sent"}]
            else:
                logger.error(f"[飞书] 卡片发送失败: {result}")
                return [{"receive_id": receive_id, "status": "failed", "error": result}]

        except Exception as e:
            logger.error(f"[飞书] 卡片发送异常: {e}")
            return [{"receive_id": receive_id, "status": "error", "error": str(e)}]
