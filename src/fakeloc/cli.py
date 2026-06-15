#!/usr/bin/env python3
"""fakeloc CLI — iPhone GPS spoofing from the terminal."""

import os
import sys
import json

from fakeloc.core import (
    PRESETS,
    TUNNEL_STATE_FILE,
    SIM_PROC_FILE,
    start_tunnel,
    set_location,
    clear_location,
    save_tunnel,
    get_tunnel,
    kill_sim_proc,
)


def cmd_up() -> bool:
    """Start the RSD tunnel (requires sudo)."""
    print("🔌 Starting tunnel (sudo required, password asked once)...")
    print()
    ok, msg, pid = start_tunnel()
    if ok:
        print(f"✅ Tunnel started!")
        print(f"   {msg}")
        if pid:
            print(f"   PID: {pid}")
        print()
        print("Ready to use:")
        print("   fakeloc sf        # San Francisco")
        print("   fakeloc nyc       # New York")
        print("   fakeloc set 35.67 139.65  # custom coords")
        return True
    else:
        print("⚠️  Could not auto-parse tunnel address, raw output:")
        for line in msg.splitlines():
            if "+q" not in line:
                print(f"   {line}")
        print()
        print("Set manually: fakeloc set-rsd <addr> <port>")
        return False


def cmd_set(lat: str | float, lon: str | float, name: str | None = None) -> None:
    """Set simulated GPS location."""
    try:
        lat_f, lon_f = float(lat), float(lon)
    except ValueError:
        print(f"❌ Invalid coordinates: {lat}, {lon}")
        return

    ok, msg = set_location(lat_f, lon_f, name)
    if ok:
        print(f"✅ {msg}")
    else:
        print(f"❌ {msg}")


def cmd_set_rsd(addr: str, port: str) -> None:
    """Manually set tunnel address."""
    save_tunnel(addr, port)
    print(f"✅ Tunnel address saved: [{addr}]:{port}")


def cmd_clear() -> None:
    """Restore real GPS location."""
    clear_location()
    print("✅ Simulation stopped, location will revert to real GPS")


def cmd_status() -> None:
    """Show current status."""
    tunnel = get_tunnel()
    if not tunnel:
        print("⚪ Tunnel not configured")
        print("   Run `fakeloc up` to start")
        return

    addr, port = tunnel
    print(f"🟢 Tunnel: [{addr}]:{port}")

    sim_running = False
    if SIM_PROC_FILE.exists():
        try:
            import signal as _signal
            pid = int(SIM_PROC_FILE.read_text().strip())
            os.kill(pid, 0)
            print(f"🟢 Simulation process: PID {pid}")
            sim_running = True
        except (ValueError, OSError):
            print("⚪ Simulation process ended")
            SIM_PROC_FILE.unlink(missing_ok=True)

    if TUNNEL_STATE_FILE.exists():
        try:
            data = json.loads(TUNNEL_STATE_FILE.read_text())
            loc = data.get("current_location")
            if loc and sim_running:
                print(f"📍 Spoofed location: {loc['name']} ({loc['lat']}, {loc['lon']})")
            elif sim_running:
                print("📍 Simulation running (coordinates not recorded)")
            else:
                print("📍 Using real location")
        except json.JSONDecodeError:
            pass


def cmd_presets() -> None:
    """List available presets."""
    print("📌 Preset locations:")
    print()
    for name, (lat, lon, desc) in sorted(PRESETS.items()):
        print(f"  {name:12s}  {lat:10.4f}, {lon:10.4f}  {desc}")
    print()
    print("Usage: fakeloc <preset>  or  fakeloc set <lat> <lon>")


def print_usage() -> None:
    print("""
fakeloc - iPhone GPS spoofing tool 🗺️

Usage:
  fakeloc up                Start tunnel (sudo, password asked once)
  fakeloc set <lat> <lon>   Set simulated location
  fakeloc <preset>          Jump to a preset location
  fakeloc clear             Restore real location
  fakeloc status            Show status
  fakeloc presets           List presets
  fakeloc set-rsd <a> <p>   Manually set tunnel address

US:    sf  nyc  la  vegas  miami  dc
Asia:  shanghai  beijing  shenzhen  tokyo  seoul  hk  taipei

Examples:
  fakeloc up               # Start tunnel (first time / after reboot)
  fakeloc sf               # Jump to San Francisco
  fakeloc nyc              # Jump to New York
  fakeloc set 35.67 139.65 # Custom coordinates
  fakeloc clear            # Restore real location
""")


def main() -> None:
    if len(sys.argv) < 2:
        print_usage()
        return

    cmd = sys.argv[1].lower()

    if cmd == "up":
        cmd_up()
    elif cmd == "set":
        if len(sys.argv) < 4:
            print("Usage: fakeloc set <latitude> <longitude> [name]")
            return
        name = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else None
        cmd_set(sys.argv[2], sys.argv[3], name)
    elif cmd == "set-rsd":
        if len(sys.argv) < 4:
            print("Usage: fakeloc set-rsd <address> <port>")
            return
        cmd_set_rsd(sys.argv[2], sys.argv[3])
    elif cmd in ("clear", "stop"):
        cmd_clear()
    elif cmd == "status":
        cmd_status()
    elif cmd == "presets":
        cmd_presets()
    elif cmd in ("--help", "-h"):
        print_usage()
    elif cmd in PRESETS:
        lat, lon, name = PRESETS[cmd]
        cmd_set(lat, lon, name)
    else:
        # Try "lat,lon" shorthand
        if "," in cmd:
            parts = cmd.split(",")
            if len(parts) == 2:
                try:
                    cmd_set(float(parts[0]), float(parts[1]))
                    return
                except ValueError:
                    pass
        print(f"❌ Unknown command: {cmd}")
        print("Run `fakeloc --help` for usage")


if __name__ == "__main__":
    main()
