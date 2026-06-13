"""
美团卡点抢券脚本 - 配置文件
"""
from datetime import datetime

# ============================================================
# ADB
# ============================================================

ADB_PATH = r"C:\Users\29543\AppData\Local\Microsoft\WinGet\Packages\Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe\platform-tools\adb.exe"
DEVICE_SERIAL = ""

# ============================================================
# 抢券参数
# ============================================================

TARGET_TIME_STR = "10:00:00"       # 抢券时间 HH:MM:SS
CLICK_X = 959                      # 按钮 X 坐标
CLICK_Y = 2598                     # 按钮 Y 坐标

LEAD_SECONDS = 15                  # 目标前 N 秒开始连点
TRAIL_MS = 5000                    # 目标后 N 毫秒停止连点
PREPARE_SECONDS = 10               # 提前 N 秒完成脚本推送

# ============================================================
# NTP 校时
# ============================================================

NTP_SERVER = "ntp.aliyun.com"
NTP_TIMEOUT = 3
OFFSET_FILE = "ntp_offset.txt"

# ============================================================
# 日志
# ============================================================

LOG_FILE = "sniper.log"
LOG_LEVEL = "INFO"

# ============================================================

def get_target_timestamp() -> float:
    h, m, s = map(int, TARGET_TIME_STR.split(":"))
    now = datetime.now()
    target = datetime(now.year, now.month, now.day, h, m, s)
    if target.timestamp() <= now.timestamp():
        from datetime import timedelta
        target += timedelta(days=1)
    return target.timestamp()
