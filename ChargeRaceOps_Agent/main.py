import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from loguru import logger

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from config import Config
from src.core.fetch import FengshuFetcher, MockFetcher
from src.core.detector import AlertDetector
from src.core.notifier import FeishuNotifier
from src.core.tracker import StateTracker
from src.core.scheduler import TaskScheduler
from src.core.recap import RecapGenerator, print_recap_summary


class ChargeRaceOpsApp:
    """
    冲锋赛过程管理 - 数据驱动业务闭环应用

    核心流程：数据采集 → 规则识别 → 精准推送 → 状态追踪 → 复盘优化
    """

    def __init__(self, use_mock: bool = True):
        self.config = Config()
        self.use_mock = use_mock

        if use_mock:
            self.fetcher = MockFetcher(self.config)
        else:
            self.fetcher = FengshuFetcher(self.config)

        self.detector = AlertDetector(self.config)
        self.notifier = FeishuNotifier(self.config)
        self.tracker = StateTracker(self.config)
        self.scheduler = TaskScheduler(self.config)
        self.recap_generator = RecapGenerator(self.config)

        self._identity_map = {}

    def run_inspection(self, mode: str = "manual"):
        """
        执行一次完整的巡检流程

        Args:
            mode: 运行模式 (peak/warmup/daily/recap/manual)
        """
        logger.info(f"[巡检] 开始执行，模式: {mode}")
        start_time = datetime.now()

        try:
            metrics = self._step_fetch(mode)
            increments = self._step_fetch_increment()

            alerts = self._step_detect(metrics, increments)

            if alerts:
                self._step_track(alerts)
                self._step_notify(alerts)

            self._step_expire_old_alerts()

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"[巡检] 完成：耗时 {elapsed:.1f}s，"
                f"采集 {len(metrics)} 条指标，"
                f"识别 {len(alerts)} 条预警"
            )

            self._print_summary(metrics, alerts)
            return alerts

        except Exception as e:
            logger.error(f"[巡检] 执行失败: {e}")
            raise

    def run_recap(self, campaign_name: str = "", save_path: str = None):
        """
        生成复盘报告

        Args:
            campaign_name: 冲锋赛名称
            save_path: 报告保存路径
        """
        logger.info(f"[复盘] 开始生成复盘报告...")

        self.tracker.expire_alerts()
        recap_data = self.tracker.get_recap_data()

        if not campaign_name:
            campaign_name = f"冲锋赛 - {datetime.now().strftime('%Y-%m-%d')}"

        report = self.recap_generator.generate(
            recap_data=recap_data,
            campaign_name=campaign_name,
            save_path=save_path,
        )

        print_recap_summary(recap_data)
        return report

    def start_scheduled(self):
        """启动定时调度模式"""
        logger.info("[调度] 启动定时巡检模式...")

        self.scheduler.register_task(
            "peak",
            lambda mode: self.run_inspection(mode),
            description="冲锋日每小时巡检",
        )
        self.scheduler.register_task(
            "warmup",
            lambda mode: self.run_inspection(mode),
            description="蓄水期每3小时巡检",
        )
        self.scheduler.register_task(
            "daily",
            lambda mode: self.run_inspection(mode),
            description="日常工作日巡检",
        )
        self.scheduler.register_task(
            "recap",
            lambda mode: self.run_recap(),
            description="每日复盘报告",
        )

        self.scheduler.start()
        logger.info("[调度] 已启动，按Ctrl+C停止")

        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.scheduler.stop()
            logger.info("[调度] 已停止")

    def _step_fetch(self, mode: str) -> list:
        """数据采集步骤"""
        logger.info("[步骤1] 数据采集...")

        levels = ["bdm", "city", "cm"]
        metrics_config = self.config.monitoring.get("metrics", [])
        metric_ids = [m["id"] for m in metrics_config]

        metrics = self.fetcher.fetch_metrics(
            levels=levels,
            metric_ids=metric_ids,
        )
        return metrics

    def _step_fetch_increment(self) -> dict:
        """获取增量数据"""
        logger.info("[步骤1b] 获取增量数据...")
        return self.fetcher.fetch_increment_data(
            metric_id="double_increment",
            hours=2,
            level="bdm",
        )

    def _step_detect(self, metrics: list, increments: dict) -> list:
        """规则识别步骤"""
        logger.info("[步骤2] 规则识别...")
        alerts = self.detector.detect(metrics, increments)
        return alerts

    def _step_track(self, alerts: list):
        """状态追踪步骤"""
        logger.info("[步骤3] 状态追踪...")
        for alert in alerts:
            self.tracker.record_alert(alert)

    def _step_notify(self, alerts: list):
        """精准推送步骤"""
        logger.info("[步骤4] 精准推送...")
        results = self.notifier.send_alerts(alerts, self._identity_map)

        success_count = sum(1 for r in results if r.get("status") == "sent")
        logger.info(f"[步骤4] 推送完成: {success_count}/{len(results)} 成功")

    def _step_expire_old_alerts(self):
        """过期处理步骤"""
        logger.info("[步骤5] 过期处理...")
        expired = self.tracker.expire_alerts()
        if expired > 0:
            logger.info(f"[步骤5] 过期处理: {expired} 条预警已过期")

    def _print_summary(self, metrics: list, alerts: list):
        """打印巡检摘要"""
        print("\n" + "=" * 60)
        print(f"📊 巡检摘要 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print(f"  采集指标: {len(metrics)} 条")
        print(f"  识别预警: {len(alerts)} 条")
        print("-" * 60)

        if alerts:
            print("  🚨 预警详情:")
            for alert in alerts[:10]:
                print(
                    f"    [{alert['rule_id']}] {alert['target_name']}/{alert['metric_name']}: "
                    f"{alert['value']:.1f}% (阈值 {alert['threshold']}%)"
                )
            if len(alerts) > 10:
                print(f"    ... 还有 {len(alerts) - 10} 条预警")
        else:
            print("  ✅ 暂无预警")

        stats = self.tracker.get_alert_stats()
        print("-" * 60)
        print(f"  📈 状态统计:")
        print(f"    总计: {stats['total']} | 待跟进: {stats['open']} | 已跟进: {stats['acknowledged']}")
        print("=" * 60 + "\n")

    def get_status(self) -> dict:
        """获取系统状态"""
        return {
            "use_mock": self.use_mock,
            "fetcher": type(self.fetcher).__name__,
            "scheduler_status": self.scheduler.get_schedule_status(),
            "alert_stats": self.tracker.get_alert_stats(),
            "rules_status": self.detector.get_rules_status(),
        }


def main():
    parser = argparse.ArgumentParser(
        description="冲锋赛过程管理 - 数据驱动业务闭环",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 单次巡检（使用Mock数据）
  python main.py run --mode manual

  # 启动定时调度（Mock模式）
  python main.py start

  # 生成复盘报告
  python main.py recap --name "618冲锋赛"

  # 查看系统状态
  python main.py status
        """,
    )

    parser.add_argument(
        "--real",
        action="store_true",
        help="使用真实API（默认使用Mock数据）",
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # run 子命令
    run_parser = subparsers.add_parser("run", help="执行一次巡检")
    run_parser.add_argument(
        "--mode",
        default="manual",
        choices=["manual", "peak", "warmup", "daily"],
        help="巡检模式",
    )

    # start 子命令
    subparsers.add_parser("start", help="启动定时巡检模式")

    # recap 子命令
    recap_parser = subparsers.add_parser("recap", help="生成复盘报告")
    recap_parser.add_argument("--name", default="", help="冲锋赛名称")
    recap_parser.add_argument("--output", default=None, help="报告保存路径")

    # status 子命令
    subparsers.add_parser("status", help="查看系统状态")

    args = parser.parse_args()

    # 配置日志
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logger.add(
        str(log_dir / "charge_race_ops.log"),
        rotation="10 MB",
        retention=5,
        level="INFO",
    )
    logger.add(sys.stdout, level="INFO")

    use_mock = not args.real

    if args.command == "run":
        app = ChargeRaceOpsApp(use_mock=use_mock)
        alerts = app.run_inspection(mode=args.mode)

    elif args.command == "start":
        app = ChargeRaceOpsApp(use_mock=use_mock)
        logger.info("🚀 启动冲锋赛过程管理系统（定时模式）")
        logger.info(f"   数据模式: {'Mock' if use_mock else '真实API'}")
        app.start_scheduled()

    elif args.command == "recap":
        app = ChargeRaceOpsApp(use_mock=use_mock)
        report = app.run_recap(
            campaign_name=args.name,
            save_path=args.output,
        )

    elif args.command == "status":
        app = ChargeRaceOpsApp(use_mock=use_mock)
        status = app.get_status()
        print("\n📋 系统状态:")
        print(f"  数据模式: {'Mock' if use_mock else '真实API'}")
        print(f"  采集器: {status['fetcher']}")
        print(f"  预警统计: {status['alert_stats']}")
        print(f"  规则状态:")
        for rule_id, rule_info in status["rules_status"].items():
            print(f"    {rule_id}: {rule_info['name']} ({rule_info['total_alerts']} 次)")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
