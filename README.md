# fakeloc

> iPhone GPS 虛拟定位工具 / iPhone GPS spoofing tool over USB

[英文](./README_EN.md) | [完整文档](./docs/README.md)

---

iPhone GPS 虛拟定位工具，基於 [pymobiledevice3](https://github.com/doronz88/pymobiledevice3)，通過 USB 連接修改 iPhone 坐標。

## 功能

- **命令行工具** (`fakeloc`) — 終端一行命令修改定位
- **圖形界面** (`fakeloc-gui`) — macOS 浮動窗口，點擊按鈕操作
- **預設位置** — 內置全球多個常用城市坐標
- **持續保持** — 自動每秒重發坐標，防止定位跳回真實位置

## 快速開始

### 安裝

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

### 基本使用

```bash
# 啟動 RSD 隧道（需 sudo）
fakeloc up

# 使用預設位置
fakeloc sf          # 舊金山
fakeloc nyc         # 紐約
fakeloc clear       # 恢復真實定位

# 圖形界面
fakeloc-gui
```

更多詳情請看 [完整文档](./docs/README.md)。

## 許可

[MIT](LICENSE)
