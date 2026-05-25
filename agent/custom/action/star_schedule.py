"""
点星调度（巡逻循环内使用，不要放在一次性入口上）。

设计：
- 巡逻节点跑完后进入 ScheduleGate，用 StarScheduleRouter 决定分支；
- 预备窗口 :25-:29 / :55-:59 → WaitUntilStar 阻塞等到 :30 / :00；
- 到点 → StarFlow（点星子流程，请自行扩展）→ 回到 Patrol_Main 继续巡逻。
"""

import time
import traceback
from datetime import datetime

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction


def is_star_prep_window(now: datetime) -> bool:
    m = now.minute
    return (25 <= m <= 29) or (55 <= m <= 59)


def is_star_fire_minute(now: datetime) -> bool:
    """整点或半点，允许前 15 秒内触发（避免错过秒级窗口）。"""
    return now.minute in (0, 30) and now.second < 15


@AgentServer.custom_action("StarScheduleRouter")
class StarScheduleRouter(CustomAction):
    """
    巡逻循环里的调度器：只负责跳转，不阻塞、不点星。
    必须配合 pipeline 里存在 WaitUntilStar / StarFlow_Entry / Patrol_Main 节点。
    """

    def run(self, context, argv) -> bool:
        try:
            now = datetime.now()
            node = argv.node_name

            if is_star_fire_minute(now):
                nxt = ["StarFlow_Entry"]
                hint = "已到点星时刻，进入点星"
            elif is_star_prep_window(now):
                nxt = ["WaitUntilStar"]
                hint = "预备窗口，进入内置等待至 :00/:30"
            else:
                nxt = ["Patrol_Continue"]
                hint = "非点星时段，继续巡逻"

            print(
                f"[StarScheduleRouter] {now.strftime('%H:%M:%S')} {hint} -> {nxt}",
                flush=True,
            )
            context.override_next(node, nxt)
            return True
        except Exception:
            print("[StarScheduleRouter] 异常:", flush=True)
            traceback.print_exc()
            return False


@AgentServer.custom_action("WaitUntilNextStar")
class WaitUntilNextStar(CustomAction):
    """内置计时：阻塞直到下一个 :00 或 :30（巡逻暂停，到点再走 next）。"""

    def run(self, context, argv) -> bool:
        try:
            print("[WaitUntilNextStar] 开始等待点星时刻 :00 / :30 …", flush=True)
            last_log = 0.0
            while True:
                now = datetime.now()
                if is_star_fire_minute(now) or now.minute in (0, 30):
                    print(
                        f"[WaitUntilNextStar] 到点 {now.strftime('%H:%M:%S')}，进入点星流程",
                        flush=True,
                    )
                    return True
                t = time.time()
                if t - last_log >= 30:
                    print(
                        f"[WaitUntilNextStar] 等待中… 当前 {now.strftime('%H:%M:%S')}",
                        flush=True,
                    )
                    last_log = t
                time.sleep(0.5)
        except Exception:
            print("[WaitUntilNextStar] 异常:", flush=True)
            traceback.print_exc()
            return False
