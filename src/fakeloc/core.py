"""
Core logic shared between the CLI and GUI.

Handles tunnel management, presets, coordinate spoofing, and process lifecycle.
"""

import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path

# ─── Configuration (overridable via environment) ────────────────────────────

def _pmd3_path() -> str:
    """Path to pymobiledevice3 binary. Override with FAKELOC_PMD3 env var."""
    return os.environ.get(
        "FAKELOC_PMD3",
        os.path.expanduser("~/fakeloc-venv/bin/pymobiledevice3"),
    )


def _askpass_path() -> str:
    """Path to the SUDO_ASKPASS helper. Override with FAKELOC_ASKPASS env var."""
    return os.environ.get(
        "FAKELOC_ASKPASS",
        os.path.expanduser("~/.local/bin/fakeloc-askpass"),
    )


TUNNEL_STATE_FILE = Path(
    os.environ.get("FAKELOC_STATE_DIR", str(Path.home()))
) / ".fakeloc_tunnel.json"

SIM_PROC_FILE = Path(
    os.environ.get("FAKELOC_STATE_DIR", str(Path.home()))
) / ".fakeloc_sim.pid"

PASSWORD_FILE = Path(os.environ.get("FAKELOC_PASSWORD_FILE", "/tmp/.fakeloc_pw"))

# ─── Presets ─────────────────────────────────────────────────────────────────
# Each entry: (lat, lon, description)

PRESETS: dict[str, tuple[float, float, str]] = {
    "home":     (25.0330, 121.5654, "Home - Taipei"),
    "taipei":   (25.0330, 121.5654, "Taipei 101"),
    "shanghai": (31.2304, 121.4737, "Shanghai Bund"),
    "beijing":  (39.9042, 116.4074, "Beijing Tiananmen"),
    "shenzhen": (22.5431, 114.0579, "Shenzhen Futian"),
    "tokyo":    (35.6762, 139.6503, "Tokyo Shibuya"),
    "seoul":    (37.5665, 126.9780, "Seoul Myeongdong"),
    "hk":       (22.3193, 114.1694, "Hong Kong Central"),
    "sf":       (37.7749, -122.4194, "San Francisco"),
    "nyc":      (40.7128, -74.0060, "New York Manhattan"),
    "london":   (51.5074, -0.1278, "London"),
    "paris":    (48.8566, 2.3522, "Paris Eiffel Tower"),
    "sydney":   (-33.8688, 151.2093, "Sydney Opera House"),
    "mars":     (4.5000, -45.0000, "Mars (simulated)"),
    "la":       (34.0522, -118.2437, "Los Angeles"),
    "vegas":    (36.1699, -115.1398, "Las Vegas"),
    "miami":    (25.7617, -80.1918, "Miami"),
    "dc":       (38.9072, -77.0369, "Washington DC"),
    "chengdu":  (30.4799, 104.0300, "Chengdu Huayang"),
    "cd":       (30.4799, 104.0300, "Chengdu Huayang"),
    "cdrcb":    (30.4799, 104.0300, "Chengdu Rural Commercial Bank"),
}

# GUI-only presets (lat/lon as strings for text fields)
GUI_PRESETS: dict[str, tuple[str, str]] = {
    "成都农商银行":      ("30.4799", "104.0300"),
    "旧金山 Apple Park": ("37.3348", "-122.0090"),
    "东京涩谷":         ("35.6595", "139.7004"),
    "纽约时代广场":      ("40.7580", "-73.9855"),
}


# ─── Tunnel state helpers ────────────────────────────────────────────────────

def get_tunnel() -> tuple[str, str] | None:
    """Return (rsd_addr, rsd_port) from the state file, or None."""
    if not TUNNEL_STATE_FILE.exists():
        return None
    try:
        data = json.loads(TUNNEL_STATE_FILE.read_text())
        return data.get("rsd_addr"), data.get("rsd_port")
    except (json.JSONDecodeError, KeyError):
        return None


def save_tunnel(addr: str, port: str) -> None:
    """Persist tunnel address/port to the state file."""
    data: dict = {}
    if TUNNEL_STATE_FILE.exists():
        try:
            data = json.loads(TUNNEL_STATE_FILE.read_text())
        except json.JSONDecodeError:
            pass
    data["rsd_addr"] = addr
    data["rsd_port"] = port
    data["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    TUNNEL_STATE_FILE.write_text(json.dumps(data, indent=2))


def kill_sim_proc() -> None:
    """Terminate any previously-running simulation process."""
    if SIM_PROC_FILE.exists():
        try:
            pid = int(SIM_PROC_FILE.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)
        except (ValueError, ProcessLookupError, OSError):
            pass
        SIM_PROC_FILE.unlink(missing_ok=True)


def parse_tunnel_output(output: str) -> tuple[str | None, str | None]:
    """Parse start-tunnel output and extract (addr, port)."""
    lines = output.strip().split("\n")
    for line in lines:
        # script-mode: "fd33:xxxx::1 53159"
        m = re.match(r"^([0-9a-f:]+)\s+(\d+)\s*$", line.strip())
        if m:
            return m.group(1), m.group(2)
    for line in lines:
        m = re.search(r"([0-9a-f:]{6,})\s+(\d{4,5})", line)
        if m:
            return m.group(1), m.group(2)
    return None, None


# ─── Tunnel management ──────────────────────────────────────────────────────

def start_tunnel() -> tuple[bool, str, int | None]:
    """
    Start the RSD tunnel via sudo.

    Returns (success, message, tunnel_pid).
    """
    pmd3 = _pmd3_path()

    # Kill any existing tunnel recorded in state file
    if TUNNEL_STATE_FILE.exists():
        try:
            data = json.loads(TUNNEL_STATE_FILE.read_text())
            old_pid = data.get("tunnel_pid")
            if old_pid:
                try:
                    os.kill(int(old_pid), signal.SIGTERM)
                    time.sleep(0.5)
                except (ValueError, ProcessLookupError, OSError):
                    pass
        except json.JSONDecodeError:
            pass

    try:
        proc = subprocess.Popen(
            ["sudo", pmd3, "remote", "start-tunnel", "--script-mode", "-t", "usb"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        output_lines: list[str] = []
        start = time.time()
        while time.time() - start < 25:
            line = proc.stdout.readline()
            if line:
                stripped = line.rstrip()
                output_lines.append(stripped)
                # Skip QUIC key lines
                if "+q" in stripped and len(stripped) > 20:
                    continue
                if "tunnel created" in stripped.lower():
                    continue
                addr, port = parse_tunnel_output("\n".join(output_lines))
                if addr and port:
                    save_tunnel(addr, port)
                    data = json.loads(TUNNEL_STATE_FILE.read_text())
                    data["tunnel_pid"] = proc.pid
                    TUNNEL_STATE_FILE.write_text(json.dumps(data, indent=2))
                    return True, f"RSD: [{addr}]:{port}", proc.pid
            else:
                time.sleep(0.3)
                if proc.poll() is not None:
                    break

        # Timeout — show raw output (minus key lines)
        visible = [l for l in output_lines if "+q" not in l]
        return False, "\n".join(visible), None

    except KeyboardInterrupt:
        return False, "Cancelled", None


def start_tunnel_with_askpass(password: str) -> tuple[bool, str]:
    """
    Start the tunnel using sudo -A with an askpass script.

    Writes the password to a temp file, sets SUDO_ASKPASS, and launches the
    tunnel.  Designed for GUI usage.

    Returns (success, status_message).
    """
    pmd3 = _pmd3_path()
    askpass = _askpass_path()

    # Write password for askpass script
    PASSWORD_FILE.write_text(password)
    os.chmod(PASSWORD_FILE, 0o600)

    # Kill existing tunnels
    subprocess.run(["pkill", "-f", "start-tunnel"], capture_output=True)

    env = os.environ.copy()
    env["SUDO_ASKPASS"] = askpass

    try:
        proc = subprocess.Popen(
            ["sudo", "-A", pmd3, "remote", "start-tunnel",
             "--script-mode", "-t", "usb"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        import select as _select

        for _ in range(30):
            ready, _, _ = _select.select([proc.stdout], [], [], 1)
            if ready:
                line = proc.stdout.readline()
                if not line:
                    break
                line = line.strip()
                if "[" in line and "]" in line:
                    idx = line.index("]")
                    addr = line[: idx + 1]
                    port = line[idx + 2 :].split()[0]
                    save_tunnel(addr, port)
                    return True, f"{addr}:{port}"
                elif line and " " in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            int(parts[-1])  # validate port
                            addr, port = parts[0], parts[-1]
                            save_tunnel(addr, port)
                            return True, f"{addr}:{port}"
                        except ValueError:
                            pass
            if proc.poll() is not None:
                err = proc.stderr.read() or ""
                return False, err.strip()[:120]

        proc.kill()
        err = proc.stderr.read() or ""
        return False, err.strip()[:120] if err.strip() else "Timeout, no address received"

    except Exception as e:
        return False, str(e)
    finally:
        try:
            PASSWORD_FILE.unlink()
        except OSError:
            pass


# ─── Location spoofing ──────────────────────────────────────────────────────

def set_location(lat: float, lon: float, name: str | None = None) -> tuple[bool, str]:
    """
    Set a simulated GPS location.

    Returns (success, message).
    """
    tunnel = get_tunnel()
    if not tunnel:
        return False, "Tunnel not configured. Run: fakeloc up"
    addr, port = tunnel

    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return False, "Coordinates out of range"

    label = name or f"({lat}, {lon})"
    kill_sim_proc()

    pmd3 = _pmd3_path()
    cmd = [pmd3, "developer", "dvt", "simulate-location", "set",
           "--rsd", addr, str(port), "--", str(lat), str(lon)]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        time.sleep(2)
        if proc.poll() is not None:
            output = proc.stdout.read()
            if "Failed to start service" in output or "tunnel" in output.lower():
                TUNNEL_STATE_FILE.unlink(missing_ok=True)
                return False, "Tunnel may have dropped. Re-run: fakeloc up"
            return False, output.strip()

        SIM_PROC_FILE.write_text(str(proc.pid))

        # Update state
        if TUNNEL_STATE_FILE.exists():
            try:
                data = json.loads(TUNNEL_STATE_FILE.read_text())
                data["current_location"] = {"lat": lat, "lon": lon, "name": label}
                TUNNEL_STATE_FILE.write_text(json.dumps(data, indent=2))
            except json.JSONDecodeError:
                pass

        return True, f"Location set to {label} ({lat}, {lon})"

    except Exception as e:
        return False, str(e)


def clear_location() -> None:
    """Stop simulation (location reverts to real GPS)."""
    kill_sim_proc()
    if TUNNEL_STATE_FILE.exists():
        try:
            data = json.loads(TUNNEL_STATE_FILE.read_text())
            data.pop("current_location", None)
            TUNNEL_STATE_FILE.write_text(json.dumps(data, indent=2))
        except json.JSONDecodeError:
            pass
