# fakeloc

> iPhone GPS 虛拟定位工具 / iPhone GPS spoofing tool over USB

[英文](./README_EN.md) | [完整文档](./docs/README.md)

---

iPhone GPS 虛拟定位工具，基於
[pymobiledevice3](https://github.com/doronz88/pymobiledevice3)，通过 USB 连接修改 iPhone 坐标。

## 功能

- **命令行工具** (`fakeloc`) — 终端一行命令修改定位
- **图形界面** (`fakeloc-gui`) — macOS 浮动窗口，点击按钮操作
- **预设位置** — 内置全球多个常用城市坐标
- **持续保持** — 自动每秒重发坐标，防止定位跳回真实位置

## 快速开始

### 安装

```bash
git clone https://github.com/MinG-98/fakeloc.git
cd fakeloc

# 创建并激活虛拟环境
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

### 基本使用

```bash
# 启动 RSD 隧道（需 sudo）
fakeloc up

# 使用预设位置
fakeloc sf          # 旧金山
fakeloc nyc         # 纽约
fakeloc clear       # 恢复真实定位

# 图形界面
fakeloc-gui
```

更多详情请看 [完整文档](./docs/README.md)。

## 许可

[MIT](LICENSE)
