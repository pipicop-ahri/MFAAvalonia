"""点星时间配置：从 pipeline custom_action_param / interface 选项读取。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

# 半点 / 整点刷星
STAR_SPAWN_MINUTES = (0, 30)


@dataclass
class StarScheduleConfig:
    minutes_before: int = 3

    def __post_init__(self) -> None:
        self.minutes_before = max(1, min(28, int(self.minutes_before)))


def _parse_param(raw) -> dict:
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return {}
        return json.loads(s)
    return {}


def load_config(context, argv) -> StarScheduleConfig:
    merged: dict = {}
    merged.update(_parse_param(getattr(argv, "custom_action_param", None)))
    if context is not None:
        node = context.get_node_data(argv.node_name)
        if node:
            action = node.get("action") or {}
            if isinstance(action, dict):
                param = action.get("param")
                if isinstance(param, dict):
                    merged.update(_parse_param(param.get("custom_action_param")))
    return StarScheduleConfig(
        minutes_before=merged.get("minutes_before", 3),
    )


def star_window_minutes(cfg: StarScheduleConfig) -> set[int]:
    """每半点/整点前 N 分钟至半点（含），如提前 3 → :27–:30、:57–:00。"""
    result: set[int] = set()
    for anchor in STAR_SPAWN_MINUTES:
        for delta in range(cfg.minutes_before + 1):
            result.add((anchor - delta) % 60)
    return result


def is_star_window(now: datetime, cfg: StarScheduleConfig) -> bool:
    return now.minute in star_window_minutes(cfg)


def is_star_spawn_minute(now: datetime) -> bool:
    """地煞刷星时刻（整点 / 半点）。"""
    return now.minute in STAR_SPAWN_MINUTES
