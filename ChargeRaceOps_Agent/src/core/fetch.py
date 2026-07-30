from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import requests
from loguru import logger

from config import Config


class FengshuFetcher:
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.base_url = self.config.get_fengshu_api_base()
        self.token = self.config.get_fengshu_api_token()
        self._cache: Dict[str, dict] = {}
        self._cache_ttl = 300

    def fetch_metrics(
        self,
        levels: List[str] = None,
        metric_ids: List[str] = None,
    ) -> List[dict]:
        """
        从风神看板拉取指定层级的指标数据

        Args:
            levels: 监控层级列表，如 ["bdm", "city", "cm"]
            metric_ids: 指标ID列表，如 ["single_complete_rate", "double_complete_rate"]

        Returns:
            指标数据列表: [{target_id, target_name, level, metric_id, metric_name, value, target_value, ts}]
        """
        if levels is None:
            levels = ["bdm", "city", "cm"]
        if metric_ids is None:
            metric_ids = [m["id"] for m in self.config.monitoring.get("metrics", [])]

        results = []
        metrics_config = self.config.monitoring.get("metrics", [])

        try:
            for metric_conf in metrics_config:
                if metric_conf["id"] not in metric_ids:
                    continue
                metric_levels = metric_conf.get("level", [])
                for level in levels:
                    if level not in metric_levels:
                        continue
                    data = self._fetch_single_metric(
                        report_id=self._get_report_id(level),
                        metric_field=metric_conf["field"],
                        metric_id=metric_conf["id"],
                        level=level,
                    )
                    results.extend(data)

            logger.info(f"[数据采集] 拉取完成: 共 {len(results)} 条指标数据")

        except Exception as e:
            logger.error(f"[数据采集] 拉取失败: {e}")
            results = self._get_cached_data(levels, metric_ids)

        return results

    def _fetch_single_metric(
        self,
        report_id: int,
        metric_field: str,
        metric_id: str,
        level: str,
    ) -> List[dict]:
        """
        拉取单个指标的数据
        实际对接风神API时，需要根据实际API文档调整参数
        """
        url = f"{self.base_url}/dashboard/report/{report_id}/query"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "metric_field": metric_field,
            "level": level,
            "filters": {},
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            results = []
            for item in data.get("data", data.get("items", [])):
                results.append({
                    "target_id": item.get("id", item.get("bdm_id", item.get("cm_id", ""))),
                    "target_name": item.get("name", item.get("bdm_name", item.get("cm_name", ""))),
                    "level": level,
                    "metric_id": metric_id,
                    "metric_name": metric_field,
                    "value": item.get("value", item.get("current", 0)),
                    "target_value": item.get("target", item.get("goal", 0)),
                    "ts": datetime.now().isoformat(),
                })

            self._update_cache(level, metric_id, results)
            return results

        except requests.exceptions.RequestException as e:
            logger.warning(f"[数据采集] API请求失败，使用缓存: {e}")
            return self._get_cached_metric(level, metric_id)

    def fetch_increment_data(
        self,
        metric_id: str,
        hours: int = 2,
        level: str = "bdm",
    ) -> Dict[str, dict]:
        """
        获取近N小时的增量数据，用于增速判断

        Returns:
            {target_id: {"values": [val_t-2, val_t-1, val_t], "increment": val_t - val_t-2}}
        """
        snapshots = {}
        now = datetime.now()

        for h in range(hours + 1):
            ts = (now - timedelta(hours=h)).strftime("%Y-%m-%d %H:00:00")
            cache_key = f"{metric_id}_{level}_{ts}"

            if cache_key in self._cache:
                snapshots[h] = self._cache[cache_key]
            else:
                snapshots[h] = {}

        increments = {}
        if len(snapshots) >= 2:
            for target_id in snapshots.get(0, {}):
                current = snapshots.get(0, {}).get(target_id, {}).get("value", 0)
                past = snapshots.get(hours, {}).get(target_id, {}).get("value", 0)
                increments[target_id] = {
                    "current": current,
                    "past": past,
                    "increment": current - past,
                    "hours": hours,
                }

        return increments

    def _get_report_id(self, level: str) -> int:
        if level == "cm":
            return self.config.dashboard.get("cm_report_id", 17421529)
        else:
            return self.config.dashboard.get("bdm_report_id", 17421549)

    def _update_cache(self, level: str, metric_id: str, data: List[dict]):
        key = f"{level}_{metric_id}"
        self._cache[key] = {
            "data": data,
            "updated_at": time.time(),
        }

    def _get_cached_metric(self, level: str, metric_id: str) -> List[dict]:
        key = f"{level}_{metric_id}"
        cached = self._cache.get(key, {})
        if cached and (time.time() - cached.get("updated_at", 0)) < self._cache_ttl:
            return cached.get("data", [])
        return []

    def _get_cached_data(
        self, levels: List[str], metric_ids: List[str]
    ) -> List[dict]:
        results = []
        for level in levels:
            for metric_id in metric_ids:
                results.extend(self._get_cached_metric(level, metric_id))
        return results


class MockFetcher(FengshuFetcher):
    """
    Mock数据获取器，用于本地开发和测试
    模拟生成BDM和CM的指标数据
    """

    def __init__(self, config: Config = None):
        super().__init__(config)
        self._mock_bdms = self._generate_mock_bdms()
        self._mock_cms = self._generate_mock_cms()

    def fetch_metrics(
        self,
        levels: List[str] = None,
        metric_ids: List[str] = None,
    ) -> List[dict]:
        if levels is None:
            levels = ["bdm", "city", "cm"]
        if metric_ids is None:
            metric_ids = [m["id"] for m in self.config.monitoring.get("metrics", [])]

        results = []
        now = datetime.now().isoformat()

        for level in levels:
            for bdm in self._mock_bdms:
                if level in ["bdm", "city"]:
                    for mid in metric_ids:
                        results.append(self._make_metric(bdm, mid, level, now))

            for cm in self._mock_cms:
                if level == "cm":
                    for mid in metric_ids:
                        results.append(self._make_metric(cm, mid, level, now))

        logger.info(f"[Mock数据] 生成 {len(results)} 条模拟指标数据")
        return results

    def _make_metric(self, target: dict, metric_id: str, level: str, ts: str) -> dict:
        value_map = {
            "single_complete_rate": target.get("single_rate", 30),
            "double_complete_rate": target.get("double_rate", 25),
            "scan_complete_rate": target.get("scan_rate", 20),
            "cm_comprehensive": target.get("comprehensive", 45),
            "double_increment": target.get("increment", 0),
        }
        target_value_map = {
            "single_complete_rate": 100,
            "double_complete_rate": 100,
            "scan_complete_rate": 100,
            "cm_comprehensive": 100,
            "double_increment": 10,
        }
        metric_name_map = {
            "single_complete_rate": "单计核销完成度",
            "double_complete_rate": "双计核销完成度",
            "scan_complete_rate": "双计扫码核销完成度",
            "cm_comprehensive": "CM综合达成",
            "double_increment": "双计核销当日增量",
        }

        return {
            "target_id": target["id"],
            "target_name": target["name"],
            "level": level,
            "metric_id": metric_id,
            "metric_name": metric_name_map.get(metric_id, metric_id),
            "value": value_map.get(metric_id, 0),
            "target_value": target_value_map.get(metric_id, 100),
            "ts": ts,
        }

    def _generate_mock_bdms(self) -> list:
        return [
            {"id": "bdm_001", "name": "王鸿鹏", "city": "杭州一区", "single_rate": 5.31, "double_rate": 9.54, "scan_rate": 3.2, "increment": 0},
            {"id": "bdm_002", "name": "朱超颖", "city": "杭州一区", "single_rate": 75.0, "double_rate": 82.5, "scan_rate": 68.0, "increment": 5},
            {"id": "bdm_003", "name": "李明", "city": "杭州二区", "single_rate": 45.0, "double_rate": 55.0, "scan_rate": 40.0, "increment": 2},
            {"id": "bdm_004", "name": "张伟", "city": "绍兴一区", "single_rate": 90.0, "double_rate": 88.0, "scan_rate": 85.0, "increment": 8},
            {"id": "bdm_005", "name": "陈静", "city": "金华一区", "single_rate": 58.0, "double_rate": 62.0, "scan_rate": 50.0, "increment": 1},
            {"id": "bdm_006", "name": "刘强", "city": "台州一区", "single_rate": 35.0, "double_rate": 40.0, "scan_rate": 30.0, "increment": 0},
            {"id": "bdm_007", "name": "黄磊", "city": "温州一区", "single_rate": 70.0, "double_rate": 75.0, "scan_rate": 65.0, "increment": 4},
            {"id": "bdm_008", "name": "周婷", "city": "宁波一区", "single_rate": 82.0, "double_rate": 78.0, "scan_rate": 80.0, "increment": 6},
        ]

    def _generate_mock_cms(self) -> list:
        return [
            {"id": "cm_001", "name": "门店A-CM", "bdm_id": "bdm_001", "comprehensive": 15.0},
            {"id": "cm_002", "name": "门店B-CM", "bdm_id": "bdm_001", "comprehensive": 45.0},
            {"id": "cm_003", "name": "门店C-CM", "bdm_id": "bdm_001", "comprehensive": 75.0},
            {"id": "cm_004", "name": "门店D-CM", "bdm_id": "bdm_002", "comprehensive": 80.0},
            {"id": "cm_005", "name": "门店E-CM", "bdm_id": "bdm_003", "comprehensive": 30.0},
            {"id": "cm_006", "name": "门店F-CM", "bdm_id": "bdm_003", "comprehensive": 65.0},
        ]
