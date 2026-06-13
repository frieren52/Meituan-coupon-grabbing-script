"""
ADB 手机控制器 — 设备检查、校时、连点脚本推送
"""
import logging
import subprocess
import tempfile
from pathlib import Path

from config import ADB_PATH, DEVICE_SERIAL

logger = logging.getLogger("sniper")


# ── 底层 ADB 命令 ──────────────────────────────────────────

def _adb_path() -> str:
    return ADB_PATH or "adb"


def _base_cmd() -> list[str]:
    cmd = [_adb_path()]
    if DEVICE_SERIAL:
        cmd += ["-s", DEVICE_SERIAL]
    return cmd


def adb(args: list[str], timeout: int = 10) -> subprocess.CompletedProcess:
    cmd = _base_cmd() + args
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def adb_raw(args: list[str], timeout: int = 10) -> bytes:
    cmd = _base_cmd() + args
    result = subprocess.run(cmd, capture_output=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"ADB: {result.stderr.decode('utf-8', errors='replace')}")
    return result.stdout


# ── 设备检查 ────────────────────────────────────────────────

def check_device() -> bool:
    result = adb(["devices"])
    lines = result.stdout.strip().split("\n")[1:]
    devices = [l for l in lines if l.strip() and "offline" not in l]
    if not devices:
        logger.error("未检测到设备，请确认 USB 调试已开启并授权")
        return False
    logger.info("设备已连接: %s", devices[0].split()[0])
    return True


# ── 手机时间 ────────────────────────────────────────────────

def get_phone_time_ms() -> int:
    result = adb(["shell", "date", "+%s%3N"])
    try:
        return int(result.stdout.strip())
    except ValueError:
        return int(adb(["shell", "date", "+%s"]).stdout.strip()) * 1000


# ── 截图 ────────────────────────────────────────────────────

def screenshot(path: str) -> None:
    data = adb_raw(["exec-out", "screencap", "-p"], timeout=10)
    Path(path).write_bytes(data)
    logger.info("截图已保存: %s", path)


# ── 连点脚本（推送到手机本地执行，零 ADB 延迟）───────────────

def push_tap_script(start_phone_ms: int, end_phone_ms: int,
                    x: int, y: int) -> None:
    script = f"""#!/system/bin/sh
START={start_phone_ms}
END={end_phone_ms}
X={x}
Y={y}

while true; do
    NOW=$(date +%s%3N 2>/dev/null || date +%s)
    if [ "$NOW" -ge "$START" ]; then
        break
    fi
done

while true; do
    NOW=$(date +%s%3N 2>/dev/null || date +%s)
    if [ "$NOW" -ge "$END" ]; then
        break
    fi
    input tap $X $Y
done
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh",
                                     delete=False, newline="\n") as f:
        f.write(script)
        tmp_path = f.name

    phone_path = "/data/local/tmp/sniper_tap.sh"
    adb(["push", tmp_path, phone_path])
    Path(tmp_path).unlink()

    cmd = _base_cmd() + ["shell",
                         f"nohup sh {phone_path} >/dev/null 2>&1 &"]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)
    duration_s = (end_phone_ms - start_phone_ms) / 1000.0
    logger.info("连点脚本已推送 (持续 %.1f 秒)", duration_s)
