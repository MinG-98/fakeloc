# fakeloc 完整文档 (中文)

> iPhone GPS 虛拟定位工具，基於 pymobiledevice3，通過 USB 連接修改 iPhone 坐標。

[英文版](./en/README.md)

## 功能

- **命令行工具** (`fakeloc`) — 終端一行命令修改定位
- **圖形界面** (`fakeloc-gui`) — macOS 浮動窗口，點擊按鈕操作
- **預設位置** — 內置全球多個常用城市坐標
- **持續保持** — 自動每秒重發坐標，防止定位跳回真實位置

## 環境要求

- macOS（已在 macOS 14+ 上測試）
- Python 3.10+
- iPhone 通過 USB 連接，已開啟開發者模式
- sudo 權限（啟動隧道需要）

## 安裝

```bash
git clone https://github.com/MinG-98/fakeloc.git
cd fakeloc

# 創建並激活虛擬環境
python3 -m venv .venv
source .venv/bin/activate

# 安裝（僅 CLI）
pip install .

# 安裝（含 GUI 支援，僅 macOS）
pip install ".[gui]"

# 安裝 sudo 密碼輔助腳本（GUI 需要）
chmod +x scripts/fakeloc-askpass
cp scripts/fakeloc-askpass ~/.local/bin/
```

### iPhone 開發者模式

首次使用需要開啟：

1. 用 USB 線將 iPhone 連接到 Mac
2. 運行 `pymobiledevice3 usbmux list` 確認設備被識別
3. 在 iPhone 上：**設置 → 隱私與安全性 → 開發者模式** → 開啟
4. iPhone 會要求重啟

## 配置

所有路徑均可通過環境變數配置：

| 環境變數 | 默認值 | 說明 |
|----------|--------|------|
| `FAKELOC_PMD3` | `~/fakeloc-venv/bin/pymobiledevice3` | pymobiledevice3 路徑 |
| `FAKELOC_ASKPASS` | `~/.local/bin/fakeloc-askpass` | sudo 密碼輔助腳本路徑 |
| `FAKELOC_STATE_DIR` | `$HOME` | 隧道狀態文件存儲目錄 |
| `FAKELOC_PASSWORD_FILE` | `/tmp/.fakeloc_pw` | sudo 密碼臨時文件路徑 |

## 使用方法

### 命令行

```bash
# 啟動 RSD 隧道（需 sudo，只輸一次密碼）
fakeloc up

# 使用預設位置
fakeloc sf          # 舊金山
fakeloc nyc         # 紐約
fakeloc tokyo       # 東京
fakeloc cdrcb       # 成都華陽

# 自定義坐標
fakeloc set 35.67 139.65

# 恢復真實定位
fakeloc clear

# 查看狀態
fakeloc status

# 列出所有預設
fakeloc presets
```

### 圖形界面

```bash
fakeloc-gui
```

1. 點擊 **啟動隧道** → 輸入 Mac 密碼
2. 選擇預設位置或輸入坐標
3. 點擊 **設定位置** — 狀態欄顯示 `✅ 定位保持中` 即成功
4. 點擊 **重置位置** 恢復真實 GPS

### 預設位置

- **美國：** `sf` `nyc` `la` `vegas` `miami` `dc`
- **亞洲：** `shanghai` `beijing` `shenzhen` `tokyo` `seoul` `hk` `taipei`
- **其他：** `london` `paris` `sydney` `mars`
- 運行 `fakeloc presets` 查看完整列表和坐標

## 工作原理

```
Mac (pymobiledevice3) --USB--> iPhone
        |
        ├── 啟動 RSD 隧道 (sudo)
        ├── 通過 DVT 服務發送模擬坐標
        └── 每秒重發保持定位穩定
```

1. `pymobiledevice3 remote start-tunnel` 通過 USB 建立 RSD 隧道
2. `pymobiledevice3 developer dvt simulate-location set` 發送 GPS 坐標
3. iPhone 的 CoreLocation 框架接收到假坐標，所有 App 都會使用它

## 局限性

- ⚠️ **僅限 GPS** — WiFi 定位、基站定位、IP 定位不受影響
- ⚠️ 部分 App 可能通過 WiFi BSSID / 基站 / IP 交叉驗證檢測到模擬
- ⚠️ iPhone 必須保持 USB 連接，斷開即恢復真實定位
- ⚠️ 首次啟動隧道需要 sudo 權限

## 許可

[MIT](LICENSE)
