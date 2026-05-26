"""
点星调度（巡逻循环 + 兰若寺找星）。

- 点星窗口：每 :00 / :30 刷星前 N 分钟（interface「点星提前」），默认 3 → :27–:30、:57–:00
- 刷星等待：到兰若寺后若未到 :00/:30，WaitUntilStarSpawn 阻塞至刷星再找星
"""

import time
import traceback
from datetime import datetime

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction

from custom.star_schedule_config import (
    is_star_spawn_minute,
    is_star_window,
    load_config,
    star_window_minutes,
)

NODE_STAR_FLOW = "bjdx_点星时段_停巡逻"
NODE_STAR_DIRECT = "bjdx_点星直链"
NODE_BEIJU_START = "bjdx_是否在北俱"
NODE_PATROL_LOOP = "bjdx_巡逻循环"
NODE_FIND_STAR = "bjdx_找星"
NODE_STAR_END = "bjdx_点星结束"


def _log(msg: str) -> None:
    print(msg, flush=True)


@AgentServer.custom_action("StarEntryRouter")
class StarEntryRouter(CustomAction):
    """任务入口：点星窗口内直接去点星，否则先挂北俱。"""

    def run(self, context, argv) -> bool:
        try:
            cfg = load_config(context, argv)
            now = datetime.now()
            if is_star_window(now, cfg):
                nxt = [NODE_STAR_DIRECT]
                hint = f"点星时段，直接去点星(提前{cfg.minutes_before}分)"
            else:
                nxt = [NODE_BEIJU_START]
                hint = "非点星时段，先挂北俱"

            _log(
                f"[bjdx][入口] {now.strftime('%H:%M:%S')} {hint} -> {nxt}"
            )
            context.override_next(argv.node_name, nxt)
            return True
        except Exception:
            _log("[bjdx][入口] StarEntryRouter 异常:")
            traceback.print_exc()
            return False


@AgentServer.custom_action("StarScheduleRouter")
class StarScheduleRouter(CustomAction):
    """巡逻循环：点星窗口停巡逻，否则继续北俱巡逻。"""

    def run(self, context, argv) -> bool:
        try:
            cfg = load_config(context, argv)
            now = datetime.now()
            if is_star_window(now, cfg):
                nxt = [NODE_STAR_FLOW]
                hint = f"点星窗口(提前{cfg.minutes_before}分)"
            else:
                nxt = [NODE_PATROL_LOOP]
                hint = "非点星时段，继续巡逻"

            _log(
                f"[bjdx][调度] {now.strftime('%H:%M:%S')} {hint} "
                f"窗口分={sorted(star_window_minutes(cfg))} -> {nxt}"
            )
            context.override_next(argv.node_name, nxt)
            return True
        except Exception:
            _log("[bjdx][调度] StarScheduleRouter 异常:")
            traceback.print_exc()
            return False


@AgentServer.custom_action("WaitUntilStarSpawn")
class WaitUntilStarSpawn(CustomAction):
    """兰若寺找星前：阻塞至 :00 / :30 刷星。"""

    def run(self, context, argv) -> bool:
        try:
            now = datetime.now()
            if is_star_spawn_minute(now):
                _log(f"[bjdx][点星] 已刷星时刻 {now.strftime('%H:%M:%S')}，开始找星")
                return True

            _log("[bjdx][点星] 等待刷星(:00/:30) …")
            last_log = 0.0
            while True:
                now = datetime.now()
                if is_star_spawn_minute(now):
                    _log(f"[bjdx][点星] 刷星时刻到 {now.strftime('%H:%M:%S')}")
                    return True
                t = time.time()
                if t - last_log >= 30:
                    _log(f"[bjdx][点星] 等待刷星… {now.strftime('%H:%M:%S')}")
                    last_log = t
                time.sleep(0.5)
        except Exception:
            _log("[bjdx][点星] WaitUntilStarSpawn 异常:")
            traceback.print_exc()
            return False


@AgentServer.custom_action("StarSearchOnError")
class StarSearchOnError(CustomAction):
    """找星未命中：仍在点星窗口则继续找星，否则结束点星回北俱。"""

    def run(self, context, argv) -> bool:
        try:
            cfg = load_config(context, argv)
            now = datetime.now()
            if is_star_window(now, cfg):
                _log(
                    f"[bjdx][点星] 未找到星，仍在点星窗口，继续找星 "
                    f"({now.strftime('%H:%M:%S')})"
                )
                context.override_next(argv.node_name, [NODE_FIND_STAR])
            else:
                _log(
                    f"[bjdx][点星] 未找到星且已出点星窗口，结束点星 "
                    f"({now.strftime('%H:%M:%S')})"
                )
                context.override_next(argv.node_name, [NODE_STAR_END])
            return True
        except Exception:
            _log("[bjdx][点星] StarSearchOnError 异常:")
            traceback.print_exc()
            return False
