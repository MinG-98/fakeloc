# 📍 fakeloc

iPhone 虚拟定位工具，基于 [pymobiledevice3](https://github.com/doronz88/pymobiledevice3)，通过 USB 修改 iPhone GPS 坐标。

## 功能

- **CLI 工具** (`fakeloc`) — 终端一行命令修改定位
- **GUI 工具** (`fakeloc_app.py`) — macOS 浮动窗口，点按钮操作
- **预设位置** — 内置全球多个常用坐标
- **持续保持** — 自动每秒重发坐标，防止定位跳回

## 环境要求

- macOS（已在 macOS 26 上测试）
- Python 3.10+
- iPhone（USB 连接，已开启开发者模式）
- sudo 权限（启动隧道需要）

## 安装

```bash
# 1. 克隆仓库
git clone https://github.com/MinG-98/fakeloc.git
cd fakeloc

# 2. 创建虚拟环境
python3 -m venv ~/fakeloc-venv
~/fakeloc-venv/bin/pip install pymobiledevice3

# 3. 设置脚本权限
chmod +x fakeloc-askpass
```

### iPhone 开发者模式

首次使用需要开启：

1. 用 USB 连接 iPhone 到 Mac
2. 运行一次 `pymobiledevice3 usbmux list`（确认设备被识别）
3. iPhone 上：**设置 → 隐私与安全性 → 开发者模式** → 开启
4. iPhone 会要求重启

## 使用方法

### CLI

```bash
# 创建快捷命令（可选）
cat > ~/.local/bin/fakeloc << 'EOF'
#!/bin/bash
exec ~/fakeloc-venv/bin/python3 /path/to/fakeloc.py "$@"
EOF
chmod +x ~/.local/bin/fakeloc

# 启动隧道（需 sudo，只输一次密码）
fakeloc up

# 设定位置
fakeloc sf          # 旧金山
fakeloc nyc         # 纽约
fakeloc tokyo       # 东京
fakeloc cdrcb       # 成都华阳
fakeloc set 35.67 139.65  # 自定义坐标

# 恢复真实定位
fakeloc clear
```

### GUI

```bash
~/fakeloc-venv/bin/python fakeloc_app.py
```

1. 点击 **启动隧道** → 输入 Mac 密码
2. 选择预设位置 → 点击 **设定位置**
3. 状态栏显示 `✅ 定位保持中` 即成功
4. 点击 **重置定位** 恢复真实位置

## 预设位置

| 命令 | 地点 | 坐标 |
|------|------|------|
| `sf` | 旧金山 | 37.7749, -122.4194 |
| `nyc` | 纽约曼哈顿 | 40.7128, -74.0060 |
| `la` | 洛杉矶 | 34.0522, -118.2437 |
| `tokyo` | 东京涩谷 | 35.6762, 139.6503 |
| `shanghai` | 上海外滩 | 31.2304, 121.4737 |
| `beijing` | 北京天安门 | 39.9042, 116.4074 |
| `cdrcb` | 成都华阳 | 30.4799, 104.0300 |
| `hk` | 香港中环 | 22.3193, 114.1694 |
| 更多... | 运行 `fakeloc presets` 查看 | |

## 工作原理

```
Mac (pymobiledevice3) --USB--> iPhone
        |
        ├── 启动 RSD 隧道 (sudo)
        ├── 通过 DVT 服务发送模拟坐标
        └── 每秒重发保持定位不掉
```

1. `pymobiledevice3 remote start-tunnel` 通过 USB 建立与 iPhone 的 RSD 隧道
2. `pymobiledevice3 developer dvt simulate-location set` 发送 GPS 坐标
3. iPhone 的 CoreLocation 框架接收到假坐标，所有 App 都会使用它

## 局限性

- ⚠️ **只能骗 GPS 坐标**，WiFi 定位、基站定位、IP 定位不受影响
- ⚠️ 国内 App（如抖音）可能通过 WiFi BSSID / 基站 / IP 识别真实位置
- ⚠️ iPhone 必须保持 USB 连接，断开即恢复真实定位
- ⚠️ 需要 sudo 权限（启动隧道时）

## 许可

MIT
