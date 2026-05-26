"""
点星调度（巡逻循环内使用）。

点星时段：每半小时的最后 3 分钟，即 :27–:30、:57–:00（含整点 :00、半点 :30）。
预备窗口：:25–:26、:55–:56，进入等待至点星时段。
"""

import time
import traceback
from datetime import datetime

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction

# 与 pipeline 节点名一致
NODE_STAR_FLOW = "bjdx_点星时段_停巡逻"
NODE_WAIT_STAR = "bjdx_等待点星"
NODE_PATROL_LOOP = "bjdx_巡逻循环"


def is_star_window(now: datetime | None = None) -> bool:
    """点星时段 :27–:30、:57–:00。"""
    if now is None:
        now = datetime.now()
    return now.minute in (0, 27, 28, 29, 30, 57, 58, 59)


def is_star_prep_window(now: datetime | None = None) -> bool:
    """点星前 2 分钟，阻塞等待进入点星时段。"""
    if now is None:
        now = datetime.now()
    return now.minute in (25, 26, 55, 56)


@AgentServer.custom_action("StarScheduleRouter")
class StarScheduleRouter(CustomAction):
    """巡逻循环调度：点星时段停巡逻，否则继续北俱巡逻。"""

    def run(self, context, argv) -> bool:
        try:
            now = datetime.now()
            if is_star_window(now):
                nxt = [NODE_STAR_FLOW]
                hint = "点星时段(:27-:30/:57-:00)"
            elif is_star_prep_window(now):
                nxt = [NODE_WAIT_STAR]
                hint = "预备窗口，等待点星时段"
            else:
                nxt = [NODE_PATROL_LOOP]
                hint = "非点星时段，继续巡逻"

            print(
                f"[bjdx][调度] {now.strftime('%H:%M:%S')} {hint} -> {nxt}",
                flush=True,
            )
            context.override_next(argv.node_name, nxt)
            return True
        except Exception:
            print("[bjdx][调度] StarScheduleRouter 异常:", flush=True)
            traceback.print_exc()
            return False


@AgentServer.custom_action("WaitUntilNextStar")
class WaitUntilNextStar(CustomAction):
    """阻塞直到进入点星时段（:27 起或 :57 起，含 :00/:30）。"""

    def run(self, context, argv) -> bool:
        try:
            print(
                "[bjdx][调度] 等待点星时段 :27-:30 / :57-:00 …",
                flush=True,
            )
            last_log = 0.0
            while True:
                now = datetime.now()
                if is_star_window(now):
                    print(
                        f"[bjdx][调度] 进入点星时段 {now.strftime('%H:%M:%S')}",
                        flush=True,
                    )
                    return True
                t = time.time()
                if t - last_log >= 30:
                    print(
                        f"[bjdx][调度] 等待中… {now.strftime('%H:%M:%S')}",
                        flush=True,
                    )
                    last_log = t
                time.sleep(0.5)
        except Exception:
            print("[bjdx][调度] WaitUntilNextStar 异常:", flush=True)
            traceback.print_exc()
            return False
