#!/usr/bin/env python3
"""美团卡点抢券 — Android 手机 ADB 方案"""

import argparse
import logging
import sys
from datetime import datetime

from sniper import CouponSniper
from config import (
    TARGET_TIME_STR, CLICK_X, CLICK_Y,
    PREPARE_SECONDS, LOG_FILE, LOG_LEVEL,
)


def setup_logging(log_file: str | None, level: str):
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
    )


def parse_time(time_str: str) -> float:
    h, m, s = map(int, time_str.split(":"))
    now = datetime.now()
    t = datetime(now.year, now.month, now.day, h, m, s)
    if t.timestamp() <= now.timestamp():
        from datetime import timedelta
        t += timedelta(days=1)
    return t.timestamp()


def main():
    p = argparse.ArgumentParser(description="美团卡点抢券脚本")
    p.add_argument("--time", default=TARGET_TIME_STR, help="抢券时间 HH:MM:SS")
    p.add_argument("--coords", nargs=2, type=int, metavar=("X", "Y"),
                   default=[CLICK_X, CLICK_Y],
                   help="点击坐标 (默认: %(default)s)")
    p.add_argument("--lead", type=int, help="目标前 N 秒开始连点")
    p.add_argument("--trail", type=int, help="目标后 N 毫秒停止连点")
    p.add_argument("--log-file", default=LOG_FILE)
    p.add_argument("--log-level", default=LOG_LEVEL)
    args = p.parse_args()

    setup_logging(args.log_file, args.log_level)
    logger = logging.getLogger("sniper")

    target_ts = parse_time(args.time)

    sniper = CouponSniper(target_ts, x=args.coords[0], y=args.coords[1])

    try:
        sniper.run()
    except KeyboardInterrupt:
        logger.info("用户中断")
    except Exception:
        logger.exception("脚本异常")


if __name__ == "__main__":
    main()
