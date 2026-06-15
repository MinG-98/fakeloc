# fakeloc

> iPhone GPS spoofing tool over USB

[English](./README_EN.md) | [中文](./README.md)

---

iPhone GPS spoofing tool over USB, powered by [pymobiledevice3](https://github.com/doronz88/pymobiledevice3).

## Features

- **CLI** (`fakeloc`) — one-liner terminal commands to change GPS coordinates
- **GUI** (`fakeloc-gui`) — native macOS floating window with preset buttons
- **Preset locations** — built-in coordinates for major cities worldwide
- **Keep-alive** — automatically resends coordinates every second to prevent GPS reversion

## Quick Start

### Installation

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

### Basic Usage

```bash
# Start the RSD tunnel (requires sudo)
fakeloc up

# Use preset
fakeloc sf          # San Francisco
fakeloc nyc         # New York
fakeloc clear       # Restore real location

# GUI
fakeloc-gui
```

For full details, configuration, presets list, how it works and limitations, see the [full documentation](./docs/en/README.md).

## License

[MIT](LICENSE)
