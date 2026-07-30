import time
import threading
from datetime import datetime
from typing import Callable, Dict, List, Optional
from loguru import logger

from config import Config


class TaskScheduler:
    """
    任务调度模块

    支持四种调度模式：
    - peak: 冲锋日每小时巡检 (0 9-22 * * *)
    - warmup: 蓄水期每3小时巡检 (0 10,13,16,19 * * *)
    - daily: 日常工作日巡检 (0 10,17 * * 1-5)
    - recap: 复盘报告生成 (30 9 * * *)
    """

    def __init__(self, config: Config = None):
        self.config = config or Config()
        self._tasks: Dict[str, dict] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._intervals: Dict[str, int] = {
            "peak": 3600,
            "warmup": 10800,
            "daily_morning": 0,
            "daily_afternoon": 0,
            "recap": 86400,
        }

    def register_task(self, mode: str, func: Callable, description: str = ""):
        """
        注册调度任务

        Args:
            mode: 调度模式 (peak/warmup/daily/recap)
            func: 要执行的函数
            description: 任务描述
        """
        self._tasks[mode] = {
            "func": func,
            "description": description,
            "last_run": None,
            "next_run": None,
        }
        logger.info(f"[调度] 注册任务: {mode} - {description}")

    def start(self):
        """启动调度器"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("[调度] 调度器已启动")

    def stop(self):
        """停止调度器"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("[调度] 调度器已停止")

    def run_once(self, mode: str = None):
        """
        手动触发一次巡检

        Args:
            mode: 指定模式，None则执行所有已注册任务
        """
        if mode:
            task = self._tasks.get(mode)
            if task:
                self._execute_task(mode, task)
        else:
            for mode_name, task in self._tasks.items():
                self._execute_task(mode_name, task)

    def _run_loop(self):
        """调度主循环"""
        while self._running:
            now = datetime.now()
            current_hour = now.hour
            current_minute = now.minute
            is_weekday = now.weekday() < 5

            for mode, task in self._tasks.items():
                if self._should_run(mode, now, current_hour, current_minute, is_weekday):
                    self._execute_task(mode, task)

            time.sleep(30)

    def _should_run(
        self,
        mode: str,
        now: datetime,
        hour: int,
        minute: int,
        is_weekday: bool,
    ) -> bool:
        """
        判断当前是否应该执行指定模式的任务

        基于配置中的cron表达式简化实现
        """
        last_run = self._tasks[mode].get("last_run")
        if last_run:
            elapsed = (now - last_run).total_seconds()
        else:
            elapsed = float("inf")

        if mode == "peak":
            if hour in range(9, 23) and minute == 0:
                return elapsed > 3500
            return False

        elif mode == "warmup":
            if hour in [10, 13, 16, 19] and minute == 0:
                return elapsed > 3500
            return False

        elif mode == "daily":
            if is_weekday and hour in [10, 17] and minute == 0:
                return elapsed > 3500
            return False

        elif mode == "recap":
            if hour == 9 and minute == 30:
                return elapsed > 3500
            return False

        return False

    def _execute_task(self, mode: str, task: dict):
        """执行任务"""
        logger.info(f"[调度] 执行任务: {mode} - {task['description']}")
        try:
            task["func"](mode)
            task["last_run"] = datetime.now()
            logger.info(f"[调度] 任务完成: {mode}")
        except Exception as e:
            logger.error(f"[调度] 任务执行失败: {mode} - {e}")

    def get_schedule_status(self) -> dict:
        """获取调度状态"""
        status = {}
        for mode, task in self._tasks.items():
            status[mode] = {
                "description": task["description"],
                "last_run": task["last_run"].isoformat() if task["last_run"] else None,
                "running": self._running,
            }
        return status


class CronScheduler:
    """
    基于schedule库的Cron调度器（更精确的时间控制）
    当需要精确到分钟级别的调度时使用
    """

    def __init__(self, config: Config = None):
        self.config = config or Config()
        self._jobs: List[dict] = []
        self._running = False

    def add_job(self, cron_expr: str, func: Callable, description: str = ""):
        """
        添加Cron任务

        Args:
            cron_expr: Cron表达式，如 "0 9 * * *"
            func: 执行函数
            description: 任务描述
        """
        job = {
            "cron": cron_expr,
            "func": func,
            "description": description,
            "enabled": True,
        }
        self._jobs.append(job)
        logger.info(f"[Cron] 添加任务: {cron_expr} - {description}")

    def start(self):
        """启动Cron调度器"""
        import schedule as sched_lib

        for job in self._jobs:
            if not job["enabled"]:
                continue

            cron = job["cron"]
            parts = cron.split()

            if len(parts) == 5:
                minute, hour, day, month, weekday = parts
                if minute == "*" and hour == "*":
                    sched_lib.every().minute.do(job["func"])
                elif hour == "*" and minute == "0":
                    sched_lib.every().hour.do(job["func"])
                elif day == "*" and month == "*":
                    if weekday == "*":
                        sched_lib.every().day.at(f"{hour}:{minute.zfill(2)}").do(job["func"])
                    else:
                        day_map = {0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday", 4: "friday", 5: "saturday", 6: "sunday"}
                        wd = day_map.get(int(weekday), "monday")
                        getattr(sched_lib.every(), wd).at(f"{hour}:{minute.zfill(2)}").do(job["func"])

        self._running = True
        threading.Thread(target=self._run_loop, daemon=True).start()
        logger.info("[Cron] 调度器已启动")

    def stop(self):
        """停止调度器"""
        self._running = False

    def _run_loop(self):
        import schedule as sched_lib
        while self._running:
            sched_lib.run_pending()
            time.sleep(1)

    def run_now(self, index: int = 0):
        """立即执行指定任务"""
        if 0 <= index < len(self._jobs):
            self._jobs[index]["func"]()
