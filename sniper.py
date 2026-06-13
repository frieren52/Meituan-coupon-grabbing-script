"""
抢券核心引擎 — NTP 校时 + 连点协调
"""
import logging
import time
from datetime import datetime
from pathlib import Path

import ntplib

from adb_controller import (
    check_device, get_phone_time_ms,
    push_tap_script, screenshot,
)
from config import (
    NTP_SERVER, NTP_TIMEOUT, OFFSET_FILE,
    LEAD_SECONDS, TRAIL_MS, PREPARE_SECONDS,
    CLICK_X, CLICK_Y, get_target_timestamp,
)

logger = logging.getLogger("sniper")


# ── NTP 时间同步 ────────────────────────────────────────────

class TimeSync:
    def __init__(self, server: str = NTP_SERVER):
        self._server = server
        self._pc_offset: float = 0.0
        self._phone_offset: float = 0.0
        self._load_offset()

    def sync(self):
        client = ntplib.NTPClient()
        try:
            resp = client.request(self._server, timeout=NTP_TIMEOUT)
            ntp = resp.tx_time
            self._pc_offset = ntp - time.time()
            self._phone_offset = ntp - get_phone_time_ms() / 1000.0
            self._save_offset()
            logger.info("NTP 同步成功  PC偏差%+.3fs  手机偏差%+.3fs",
                        self._pc_offset, self._phone_offset)
        except Exception as e:
            logger.warning("NTP 同步失败: %s，使用缓存偏移", e)

    def precise_time(self) -> float:
        return time.time() + self._pc_offset

    def phone_ms(self, ntp_s: float) -> int:
        return int((ntp_s - self._phone_offset) * 1000)

    def wait_until(self, target: float):
        while True:
            r = target - self.precise_time()
            if r <= 0:
                return
            if r > 0.1:
                time.sleep(0.05)
            elif r > 0.01:
                time.sleep(0.005)
            else:
                while self.precise_time() < target:
                    pass
                return

    def _save_offset(self):
        Path(OFFSET_FILE).write_text(
            f"{self._pc_offset}\n{self._phone_offset}")

    def _load_offset(self):
        p = Path(OFFSET_FILE)
        if p.exists():
            try:
                lines = p.read_text().strip().split("\n")
                self._pc_offset = float(lines[0])
                self._phone_offset = float(lines[1]) if len(lines) > 1 else 0.0
                logger.info("加载缓存偏移 PC=%+.3fs 手机=%+.3fs",
                            self._pc_offset, self._phone_offset)
            except (ValueError, IOError):
                pass


# ── 抢券引擎 ────────────────────────────────────────────────

class CouponSniper:
    def __init__(self, target_ts: float | None = None,
                 x: int = CLICK_X, y: int = CLICK_Y):
        self._target = target_ts or get_target_timestamp()
        self._x = x
        self._y = y
        self._ts = TimeSync()

    def run(self) -> dict:
        target_dt = datetime.fromtimestamp(self._target)
        logger.info("=" * 50)
        logger.info("美团卡点抢券  %s  坐标(%d, %d)",
                    target_dt.strftime("%H:%M:%S"), self._x, self._y)

        # 1. 设备 & 校时
        if not check_device():
            return {"success": False, "error": "设备未连接"}
        self._ts.sync()

        # 2. 计算窗口
        click_start = self._target - LEAD_SECONDS
        click_end = self._target + TRAIL_MS / 1000.0
        push_at = click_start - PREPARE_SECONDS

        now = self._ts.precise_time()
        if now >= push_at:
            logger.warning("推送截止时间已过，立即执行")

        # 3. 等待→推送
        if push_at > now:
            self._ts.wait_until(push_at)

        phone_start = self._ts.phone_ms(click_start)
        phone_end = self._ts.phone_ms(click_end)

        logger.info("连点窗口 %s → %s",
                    datetime.fromtimestamp(click_start).strftime("%H:%M:%S.%f")[:-3],
                    datetime.fromtimestamp(click_end).strftime("%H:%M:%S.%f")[:-3])

        push_tap_script(phone_start, phone_end, self._x, self._y)

        # 4. 等待结束并截图
        remain = click_end - self._ts.precise_time()
        if remain > 0:
            self._ts.wait_until(click_end + 0.5)

        time.sleep(0.5)
        try:
            screenshot("result.png")
        except Exception as e:
            logger.warning("截图失败: %s", e)

        logger.info("=" * 50)
        logger.info("抢券完成  坐标(%d, %d)", self._x, self._y)
        return {"success": True, "coords": (self._x, self._y),
                "target": self._target}
