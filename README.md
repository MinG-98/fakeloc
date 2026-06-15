# fakeloc

iPhone GPS 虚拟定位工具 / iPhone GPS spoofing tool over USB

[English](#english) | [中文](#中文)

---

## English

iPhone GPS spoofing tool over USB, powered by
[pymobiledevice3](https://github.com/doronz88/pymobiledevice3).

### Features

- **CLI** (`fakeloc`) — one-liner terminal commands to change GPS coordinates
- **GUI** (`fakeloc-gui`) — native macOS floating window with preset buttons
- **Preset locations** — built-in coordinates for major cities worldwide
- **Keep-alive** — automatically resends coordinates every second to prevent GPS reversion

### Requirements

- macOS (tested on macOS 14+)
- Python 3.10+
- iPhone connected via USB with Developer Mode enabled
- sudo access (required to start the RSD tunnel)

### Installation

#### From source

```bash
git clone https://github.com/MinG-98/fakeloc.git
cd fakeloc

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install (CLI only)
pip install .

# Install with GUI support (macOS only)
pip install ".[gui]"

# Install the askpass helper (for GUI sudo)
chmod +x scripts/fakeloc-askpass
cp scripts/fakeloc-askpass ~/.local/bin/
```

#### Using pipx (CLI only)

```bash
pipx install .
```

### Configuration

All paths are configurable via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `FAKELOC_PMD3` | `~/fakeloc-venv/bin/pymobiledevice3` | Path to pymobiledevice3 binary |
| `FAKELOC_ASKPASS` | `~/.local/bin/fakeloc-askpass` | Path to sudo askpass helper |
| `FAKELOC_STATE_DIR` | `$HOME` | Directory for tunnel state file |
| `FAKELOC_PASSWORD_FILE` | `/tmp/.fakeloc_pw` | Temp file for sudo password |

### iPhone Developer Mode

Required on first use:

1. Connect iPhone to Mac via USB
2. Run `pymobiledevice3 usbmux list` to verify the device is recognized
3. On iPhone: **Settings → Privacy & Security → Developer Mode** → Enable
4. iPhone will require a restart

### Usage

#### CLI

```bash
# Start the RSD tunnel (requires sudo, password asked once)
fakeloc up

# Set location by preset
fakeloc sf          # San Francisco
fakeloc nyc         # New York
fakeloc tokyo       # Tokyo
fakeloc cdrcb       # Chengdu

# Set custom coordinates
fakeloc set 35.67 139.65

# Restore real location
fakeloc clear

# Check status
fakeloc status

# List all presets
fakeloc presets
```

#### GUI

```bash
fakeloc-gui
```

1. Click **Start Tunnel** → enter your Mac password
2. Select a preset or enter coordinates
3. Click **Set Location** — status shows `✅ Location held` when active
4. Click **Reset Location** to restore real GPS

### Preset Locations

- **US:** `sf` `nyc` `la` `vegas` `miami` `dc`
- **Asia:** `shanghai` `beijing` `shenzhen` `tokyo` `seoul` `hk` `taipei`
- **Other:** `london` `paris` `sydney` `mars`
- Run `fakeloc presets` for the full list with coordinates

### How It Works

```
Mac (pymobiledevice3) --USB--> iPhone
        |
        ├── Start RSD tunnel (sudo)
        ├── Send simulated coordinates via DVT service
        └── Resend every second to keep location stable
```

1. `pymobiledevice3 remote start-tunnel` establishes an RSD tunnel over USB
2. `pymobiledevice3 developer dvt simulate-location set` sends GPS coordinates
3. iPhone's CoreLocation framework receives the spoofed coordinates — all apps use them

### Limitations

- ⚠️ **GPS only** — WiFi positioning, cell tower triangulation, and IP geolocation are not affected
- ⚠️ Some apps may detect spoofing via WiFi BSSID / cell tower / IP cross-check
- ⚠️ iPhone must remain USB-connected; disconnecting restores real location
- ⚠️ Requires sudo access for the initial tunnel setup

---

## 中文

基于 [pymobiledevice3](https://github.com/doronz88/pymobiledevice3) 的 iPhone GPS 虚拟定位工具，通过 USB 连接修改 iPhone 坐标。

### 功能

- **命令行工具** (`fakeloc`) — 终端一行命令修改定位
- **图形界面** (`fakeloc-gui`) — macOS 浮动窗口，点击按钮操作
- **预设位置** — 内置全球多个常用城市坐标
- **持续保持** — 自动每秒重发坐标，防止定位跳回真实位置

### 环境要求

- macOS（已在 macOS 14+ 上测试）
- Python 3.10+
- iPhone 通过 USB 连接，已开启开发者模式
- sudo 权限（启动隧道需要）

### 安装

#### 从源码安装

```bash
git clone https://github.com/MinG-98/fakeloc.git
cd fakeloc

# 创建并激活虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装（仅 CLI）
pip install .

# 安装（含 GUI 支持，仅 macOS）
pip install ".[gui]"

# 安装 sudo 密码辅助脚本（GUI 需要）
chmod +x scripts/fakeloc-askpass
cp scripts/fakeloc-askpass ~/.local/bin/
```

#### 使用 pipx（仅 CLI）

```bash
pipx install .
```

### 配置

所有路径均可通过环境变量配置：

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `FAKELOC_PMD3` | `~/fakeloc-venv/bin/pymobiledevice3` | pymobiledevice3 可执行文件路径 |
| `FAKELOC_ASKPASS` | `~/.local/bin/fakeloc-askpass` | sudo 密码辅助脚本路径 |
| `FAKELOC_STATE_DIR` | `$HOME` | 隧道状态文件存储目录 |
| `FAKELOC_PASSWORD_FILE` | `/tmp/.fakeloc_pw` | sudo 密码临时文件路径 |

### iPhone 开发者模式

首次使用需要开启：

1. 用 USB 线将 iPhone 连接到 Mac
2. 运行 `pymobiledevice3 usbmux list` 确认设备被识别
3. 在 iPhone 上：**设置 → 隐私与安全性 → 开发者模式** → 开启
4. iPhone 会要求重启

### 使用方法

#### 命令行

```bash
# 启动 RSD 隧道（需 sudo，只输一次密码）
fakeloc up

# 使用预设位置
fakeloc sf          # 旧金山
fakeloc nyc         # 纽约
fakeloc tokyo       # 东京
fakeloc cdrcb       # 成都华阳

# 自定义坐标
fakeloc set 35.67 139.65

# 恢复真实定位
fakeloc clear

# 查看状态
fakeloc status

# 列出所有预设
fakeloc presets
```

#### 图形界面

```bash
fakeloc-gui
```

1. 点击 **启动隧道** → 输入 Mac 密码
2. 选择预设位置或输入坐标
3. 点击 **设定位置** — 状态栏显示 `✅ 定位保持中` 即成功
4. 点击 **重置定位** 恢复真实 GPS

### 预设位置

- **美国：** `sf` `nyc` `la` `vegas` `miami` `dc`
- **亚洲：** `shanghai` `beijing` `shenzhen` `tokyo` `seoul` `hk` `taipei`
- **其他：** `london` `paris` `sydney` `mars`
- 运行 `fakeloc presets` 查看完整列表和坐标

### 工作原理

```
Mac (pymobiledevice3) --USB--> iPhone
        |
        ├── 启动 RSD 隧道 (sudo)
        ├── 通过 DVT 服务发送模拟坐标
        └── 每秒重发保持定位稳定
```

1. `pymobiledevice3 remote start-tunnel` 通过 USB 建立 RSD 隧道
2. `pymobiledevice3 developer dvt simulate-location set` 发送 GPS 坐标
3. iPhone 的 CoreLocation 框架接收到假坐标，所有 App 都会使用它

### 局限性

- ⚠️ **仅限 GPS** — WiFi 定位、基站定位、IP 定位不受影响
- ⚠️ 部分 App 可能通过 WiFi BSSID / 基站 / IP 交叉验证检测到模拟
- ⚠️ iPhone 必须保持 USB 连接，断开即恢复真实定位
- ⚠️ 首次启动隧道需要 sudo 权限

---

## License | 许可

[MIT](LICENSE)
