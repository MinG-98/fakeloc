# fakeloc

iPhone GPS spoofing tool over USB, powered by
[pymobiledevice3](https://github.com/doronz88/pymobiledevice3).

## Features

- **CLI** (`fakeloc`) — one-liner terminal commands to change GPS coordinates
- **GUI** (`fakeloc-gui`) — native macOS floating window with preset buttons
- **Preset locations** — built-in coordinates for major cities worldwide
- **Keep-alive** — automatically resends coordinates every second to prevent GPS reversion

## Requirements

- macOS (tested on macOS 14+)
- Python 3.10+
- iPhone connected via USB with Developer Mode enabled
- sudo access (required to start the RSD tunnel)

## Installation

### From source

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

### Using pipx (CLI only)

```bash
pipx install .
```

## Configuration

All paths are configurable via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `FAKELOC_PMD3` | `~/fakeloc-venv/bin/pymobiledevice3` | Path to pymobiledevice3 binary |
| `FAKELOC_ASKPASS` | `~/.local/bin/fakeloc-askpass` | Path to sudo askpass helper |
| `FAKELOC_STATE_DIR` | `$HOME` | Directory for tunnel state file |
| `FAKELOC_PASSWORD_FILE` | `/tmp/.fakeloc_pw` | Temp file for sudo password |

## iPhone Developer Mode

Required on first use:

1. Connect iPhone to Mac via USB
2. Run `pymobiledevice3 usbmux list` to verify the device is recognized
3. On iPhone: **Settings → Privacy & Security → Developer Mode** → Enable
4. iPhone will require a restart

## Usage

### CLI

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

### GUI

```bash
fakeloc-gui
```

1. Click **Start Tunnel** → enter your Mac password
2. Select a preset or enter coordinates
3. Click **Set Location** — status shows `✅ Location held` when active
4. Click **Reset Location** to restore real GPS

## Preset Locations

- **US:** `sf` `nyc` `la` `vegas` `miami` `dc`
- **Asia:** `shanghai` `beijing` `shenzhen` `tokyo` `seoul` `hk` `taipei`
- **Other:** `london` `paris` `sydney` `mars`
- Run `fakeloc presets` for the full list with coordinates

## How It Works

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

## Limitations

- ⚠️ **GPS only** — WiFi positioning, cell tower triangulation, and IP geolocation are not affected
- ⚠️ Some apps may detect spoofing via WiFi BSSID / cell tower / IP cross-check
- ⚠️ iPhone must remain USB-connected; disconnecting restores real location
- ⚠️ Requires sudo access for the initial tunnel setup

## License

[MIT](LICENSE)
