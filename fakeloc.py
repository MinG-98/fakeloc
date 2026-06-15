#!/usr/bin/env python3
"""
fakeloc - iPhone 虚拟定位工具
基于 pymobiledevice3，通过 USB 修改 iPhone GPS 定位

用法:
  fakeloc up              启动隧道 + 保存地址（需 sudo，只输一次密码）
  fakeloc set <lat> <lon> 设置定位
  fakeloc clear           恢复真实定位
  fakeloc <预设名>         跳到预设位置
  fakeloc stop            停止定位模拟
  fakeloc status          查看状态
"""

import subprocess
import sys
import os
import json
import signal
import time
import re
from pathlib import Path

# ─── 配置 ───
PMD3 = os.path.expanduser("~/fakeloc-venv/bin/pymobiledevice3")
TUNNEL_STATE_FILE = Path.home() / ".fakeloc_tunnel.json"
SIM_PROC_FILE = Path.home() / ".fakeloc_sim.pid"

# ─── 预设位置 ───
PRESETS = {
    "home":     (25.0330, 121.5654, "家 - 台北"),
    "taipei":   (25.0330, 121.5654, "台北 101"),
    "shanghai": (31.2304, 121.4737, "上海外滩"),
    "beijing":  (39.9042, 116.4074, "北京天安门"),
    "shenzhen": (22.5431, 114.0579, "深圳福田"),
    "tokyo":    (35.6762, 139.6503, "东京涩谷"),
    "seoul":    (37.5665, 126.9780, "首尔明洞"),
    "hk":       (22.3193, 114.1694, "香港中环"),
    "sf":       (37.7749, -122.4194, "旧金山"),
    "nyc":      (40.7128, -74.0060, "纽约曼哈顿"),
    "london":   (51.5074, -0.1278, "伦敦"),
    "paris":    (48.8566, 2.3522, "巴黎埃菲尔铁塔"),
    "sydney":   (-33.8688, 151.2093, "悉尼歌剧院"),
    "mars":     (4.5000, -45.0000, "火星 (模拟)"),
    "la":       (34.0522, -118.2437, "洛杉矶"),
    "vegas":    (36.1699, -115.1398, "拉斯维加斯"),
    "miami":    (25.7617, -80.1918, "迈阿密"),
    "dc":       (38.9072, -77.0369, "华盛顿DC"),
    "chengdu":  (30.4799, 104.0300, "成都华阳祥鹤四街105号"),
    "cd":       (30.4799, 104.0300, "成都华阳鹤林分理处"),
    "cdrcb":    (30.4799, 104.0300, "成都农商银行华阳鹤林分理处"),
}


def get_tunnel():
    """获取隧道地址，返回 (addr, port) 或 None"""
    if not TUNNEL_STATE_FILE.exists():
        return None
    try:
        data = json.loads(TUNNEL_STATE_FILE.read_text())
        return data.get("rsd_addr"), data.get("rsd_port")
    except (json.JSONDecodeError, KeyError):
        return None


def save_tunnel(addr, port):
    """保存隧道信息"""
    data = {}
    if TUNNEL_STATE_FILE.exists():
        try:
            data = json.loads(TUNNEL_STATE_FILE.read_text())
        except json.JSONDecodeError:
            pass
    data["rsd_addr"] = addr
    data["rsd_port"] = port
    data["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    TUNNEL_STATE_FILE.write_text(json.dumps(data, indent=2))


def kill_sim_proc():
    """停止之前的模拟进程"""
    if SIM_PROC_FILE.exists():
        try:
            pid = int(SIM_PROC_FILE.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)
        except (ValueError, ProcessLookupError, OSError):
            pass
        SIM_PROC_FILE.unlink(missing_ok=True)


def parse_tunnel_output(output):
    """解析 start-tunnel 输出，提取地址和端口"""
    lines = output.strip().split('\n')
    for line in lines:
        # script-mode: "fd33:xxxx::1 53159"
        m = re.match(r'^([0-9a-f:]+)\s+(\d+)\s*$', line.strip())
        if m:
            return m.group(1), m.group(2)
    for line in lines:
        m = re.search(r'([0-9a-f:]{6,})\s+(\d{4,5})', line)
        if m:
            return m.group(1), m.group(2)
    return None, None


def cmd_up():
    """启动隧道并自动保存地址（一条命令搞定）"""
    print("🔌 启动隧道（需要 sudo，只输一次密码）...")
    print()

    # 先 kill 旧的 tunnel 进程
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
            ["sudo", PMD3, "remote", "start-tunnel", "--script-mode", "-t", "usb"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        output_lines = []
        start = time.time()
        while time.time() - start < 25:
            line = proc.stdout.readline()
            if line:
                stripped = line.rstrip()
                output_lines.append(stripped)
                # 跳过加密码行（包含 +q 的是 QUIC 密钥）
                if '+q' in stripped and len(stripped) > 20:
                    continue
                if 'tunnel created' in stripped.lower():
                    continue
                # 尝试解析地址
                addr, port = parse_tunnel_output('\n'.join(output_lines))
                if addr and port:
                    save_tunnel(addr, port)
                    # 保存 tunnel PID
                    data = json.loads(TUNNEL_STATE_FILE.read_text())
                    data["tunnel_pid"] = proc.pid
                    TUNNEL_STATE_FILE.write_text(json.dumps(data, indent=2))

                    print(f"✅ 隧道已启动！")
                    print(f"   RSD: [{addr}]:{port}")
                    print(f"   PID: {proc.pid}")
                    print()
                    print(f"现在可以直接用了：")
                    print(f"   fakeloc sf        # 旧金山")
                    print(f"   fakeloc nyc       # 纽约")
                    print(f"   fakeloc set 35.67 139.65  # 自定义坐标")
                    return True
            else:
                time.sleep(0.3)
                if proc.poll() is not None:
                    break

        # 超时
        print("⚠️  未能自动解析隧道地址，原始输出：")
        for line in output_lines:
            if '+q' not in line:  # 跳过密钥行
                print(f"   {line}")
        print()
        print("请手动设置: fakeloc set-rsd <地址> <端口>")
        return False

    except KeyboardInterrupt:
        print("\n已取消")
        return False


def cmd_set(lat, lon, name=None):
    """设置虚拟定位"""
    tunnel = get_tunnel()
    if not tunnel:
        print("❌ 隧道未配置。先运行: fakeloc up")
        return False

    addr, port = tunnel
    try:
        lat_f, lon_f = float(lat), float(lon)
    except ValueError:
        print(f"❌ 无效坐标: {lat}, {lon}")
        return False

    if not (-90 <= lat_f <= 90) or not (-180 <= lon_f <= 180):
        print(f"❌ 坐标超出范围")
        return False

    label = name or f"({lat_f}, {lon_f})"
    print(f"📍 定位到: {label}")
    print(f"   坐标: {lat_f}, {lon_f}")

    # 停止旧模拟进程
    kill_sim_proc()

    cmd = [PMD3, "developer", "dvt", "simulate-location", "set",
           "--rsd", addr, str(port),
           "--", str(lat_f), str(lon_f)]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        time.sleep(2)
        if proc.poll() is not None:
            output = proc.stdout.read()
            # 检查是否是隧道断了
            if "Failed to start service" in output or "tunnel" in output.lower():
                print("❌ 隧道可能断了，请重新运行: fakeloc up")
                TUNNEL_STATE_FILE.unlink(missing_ok=True)
            else:
                print(f"❌ 失败: {output.strip()}")
            return False

        SIM_PROC_FILE.write_text(str(proc.pid))

        # 更新状态
        if TUNNEL_STATE_FILE.exists():
            data = json.loads(TUNNEL_STATE_FILE.read_text())
            data["current_location"] = {"lat": lat_f, "lon": lon_f, "name": label}
            TUNNEL_STATE_FILE.write_text(json.dumps(data, indent=2))

        print(f"✅ 定位已设置！ (旧金山 → {label})")
        return True

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def cmd_set_rsd(addr, port):
    """手动设置隧道地址"""
    save_tunnel(addr, port)
    print(f"✅ 隧道地址已保存: [{addr}]:{port}")


def cmd_clear():
    """恢复真实定位"""
    kill_sim_proc()
    print("✅ 模拟进程已停止，定位将自动恢复真实")
    if TUNNEL_STATE_FILE.exists():
        try:
            data = json.loads(TUNNEL_STATE_FILE.read_text())
            data.pop("current_location", None)
            TUNNEL_STATE_FILE.write_text(json.dumps(data, indent=2))
        except json.JSONDecodeError:
            pass


def cmd_status():
    """显示状态"""
    tunnel = get_tunnel()
    if not tunnel:
        print("⚪ 隧道未配置")
        print("   运行 `fakeloc up` 启动")
        return

    addr, port = tunnel
    print(f"🟢 隧道: [{addr}]:{port}")

    # 检查模拟进程
    sim_running = False
    if SIM_PROC_FILE.exists():
        try:
            pid = int(SIM_PROC_FILE.read_text().strip())
            os.kill(pid, 0)
            print(f"🟢 模拟进程: PID {pid}")
            sim_running = True
        except (ValueError, OSError):
            print(f"⚪ 模拟进程已结束")
            SIM_PROC_FILE.unlink(missing_ok=True)

    if TUNNEL_STATE_FILE.exists():
        data = json.loads(TUNNEL_STATE_FILE.read_text())
        loc = data.get("current_location")
        if loc and sim_running:
            print(f"📍 虚拟定位: {loc['name']} ({loc['lat']}, {loc['lon']})")
        elif sim_running:
            print(f"📍 模拟运行中（未记录坐标）")
        else:
            print(f"📍 使用真实定位")


def cmd_presets():
    """列出预设"""
    print("📌 预设位置:")
    print()
    for name, (lat, lon, desc) in sorted(PRESETS.items()):
        print(f"  {name:12s}  {lat:10.4f}, {lon:10.4f}  {desc}")
    print()
    print("用法: fakeloc <预设名>  或  fakeloc set <lat> <lon>")


def print_usage():
    print("""
fakeloc - iPhone 虚拟定位工具 🗺️

用法:
  fakeloc up                启动隧道（需 sudo，只输一次密码）
  fakeloc set <lat> <lon>   设置虚拟定位
  fakeloc <预设名>           跳到预设位置
  fakeloc clear             恢复真实定位
  fakeloc status            查看状态
  fakeloc presets           列出预设

美国:  sf  nyc  la  vegas  miami  dc
亚洲:  shanghai  beijing  shenzhen  tokyo  seoul  hk  taipei

示例:
  fakeloc up          # 启动隧道（首次/换手机/重启后）
  fakeloc sf          # 跳到旧金山
  fakeloc nyc         # 跳到纽约
  fakeloc set 35.67 139.65  # 自定义坐标
  fakeloc clear       # 恢复真实定位
""")


def main():
    if len(sys.argv) < 2:
        print_usage()
        return

    cmd = sys.argv[1].lower()

    if cmd == "up":
        cmd_up()
    elif cmd == "set":
        if len(sys.argv) < 4:
            print("用法: fakeloc set <纬度> <经度> [名称]")
            return
        name = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else None
        cmd_set(sys.argv[2], sys.argv[3], name)
    elif cmd == "set-rsd":
        if len(sys.argv) < 4:
            print("用法: fakeloc set-rsd <地址> <端口>")
            return
        cmd_set_rsd(sys.argv[2], sys.argv[3])
    elif cmd == "clear":
        cmd_clear()
    elif cmd == "stop":
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
        if "," in cmd:
            parts = cmd.split(",")
            if len(parts) == 2:
                try:
                    cmd_set(float(parts[0]), float(parts[1]))
                    return
                except ValueError:
                    pass
        print(f"❌ 未知: {cmd}")
        print("运行 `fakeloc --help` 查看用法")


if __name__ == "__main__":
    main()
