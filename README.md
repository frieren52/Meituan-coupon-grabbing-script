# 美团卡点抢券脚本

Android 物理手机 + ADB 方案。在目标时刻前后连续点击固定坐标，实现卡点抢券。

## 环境准备

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 安装 ADB

```bash
winget install Google.PlatformTools
```

安装后重启终端，确认生效：

```bash
adb version
```

### 3. 手机开启 USB 调试

1. 设置 → 关于手机 → 连续点击 **版本号** 7 次，进入开发者模式
2. 设置 → 开发者选项 → 开启 **USB 调试**
3. 数据线连接电脑，手机上点 **允许**

验证连接：

```bash
adb devices
```

输出 `xxxxxxxx  device` 即表示成功。

## 获取按钮坐标

1. 手机开发者选项 → 开启 **指针位置**
2. 打开美团 App，进入抢券页面
3. 点击抢券按钮位置，屏幕顶部会显示 X/Y 坐标
4. 记下坐标，写入 `config.py` 的 `CLICK_X` / `CLICK_Y`

本机已配置坐标：**(959, 2598)**

## 使用

### 命令行

```bash
# 使用 config.py 默认时间
python main.py

# 指定时间
python main.py --time "10:00:00"

# 覆盖坐标
python main.py --time "10:00:00" --coords 600 2100
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--time` | 抢券时间 HH:MM:SS | `10:00:00` |
| `--coords X Y` | 点击坐标 | `959 2598` |
| `--lead` | 目标前 N 秒开始连点 | `15` |
| `--trail` | 目标后 N 毫秒停止 | `5000` |

### 抢券前检查清单

- [ ] 数据线已连接，`adb devices` 可见设备
- [ ] 手机屏幕保持亮着（息屏会阻断点击）
- [ ] 美团 App 已打开并停留在抢券页面
- [ ] 时间正确（如果是今天下午的券，确保日期匹配）

## 工作原理

```
目标前 10s → 推送 shell 脚本到手机
目标前 15s → 手机本地 busy-wait，开始连点
   ... 快速 input tap ...
目标后 5s  → 停止连点
```

脚本在手机本地执行，不经过 ADB 通信，延迟极小。NTP 校时确保手机时钟与标准时间对齐。

## 配置项

编辑 `config.py`：

| 配置 | 说明 |
|------|------|
| `TARGET_TIME_STR` | 默认抢券时间 |
| `CLICK_X / CLICK_Y` | 默认点击坐标 |
| `LEAD_SECONDS` | 提前开始连点秒数 |
| `TRAIL_MS` | 目标后继续连点毫秒数 |
| `PREPARE_SECONDS` | 提前推送脚本秒数 |
