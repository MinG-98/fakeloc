#!/usr/bin/env python3
"""fakeloc — 最简测试"""
import objc
from AppKit import NSApplication, NSWindow, NSApp, NSBackingStoreBuffered
from AppKit import NSWindowStyleMaskTitled, NSWindowStyleMaskClosable
from AppKit import NSApplicationActivationPolicyAccessory, NSButton, NSTextField, NSFont
from AppKit import NSBezelStyleRounded, NSColor
from Foundation import NSObject, NSMakeRect, NSRunLoop, NSDate
import subprocess, os, threading, select

PMD3 = os.path.expanduser("~/fakeloc-venv/bin/pymobiledevice3")
rsd_addr = None
rsd_port = None
keep_alive = False  # 持续发送定位的开关

PRESETS = {
    "成都农商银行": ("30.4799", "104.0300"),
    "旧金山 Apple Park": ("37.3348", "-122.0090"),
    "东京涩谷": ("35.6595", "139.7004"),
    "纽约时代广场": ("40.7580", "-73.9855"),
}


class App(NSObject):
    win = objc.ivar()
    statusLbl = objc.ivar()
    latFld = objc.ivar()
    lonFld = objc.ivar()
    presetBtns = objc.ivar()
    isRunning = objc.ivar()

    def applicationDidFinishLaunching_(self, note):
        self.isRunning = False
        self.presetBtns = {}

        self.win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(200, 200, 420, 420),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered, False
        )
        self.win.setTitle_("📍 fakeloc - iPhone 虚拟定位")
        self.win.setLevel_(3)

        c = self.win.contentView()
        y = 380

        # 状态
        self.statusLbl = self._lbl("检测设备中...", 12, NSColor.secondaryLabelColor())
        self.statusLbl.setFrame_(NSMakeRect(20, y, 380, 20))
        c.addSubview_(self.statusLbl)
        y -= 30

        # 分隔
        sep = self._sep(y)
        c.addSubview_(sep)
        y -= 20

        # 常用位置
        c.addSubview_(self._lbl_at("常用位置", 14, True, 20, y))
        y -= 30

        for name, (lat, lon) in PRESETS.items():
            btn = NSButton.alloc().initWithFrame_(NSMakeRect(20, y, 380, 26))
            btn.setTitle_(name)
            btn.setBezelStyle_(NSBezelStyleRounded)
            btn.setTarget_(self)
            btn.setAction_(objc.selector(self.presetClicked_, signature=b"v@:@"))
            btn.setFont_(NSFont.systemFontOfSize_(13))
            btn.setTag_(len(self.presetBtns))
            self.presetBtns[btn.tag()] = (lat, lon)
            c.addSubview_(btn)
            y -= 30

        y -= 5
        c.addSubview_(self._sep(y))
        y -= 25

        # 坐标输入
        c.addSubview_(self._lbl_at("坐标 (WGS-84)", 14, True, 20, y))
        y -= 28

        self.latFld = self._field(20, y, 170, "纬度 30.4799")
        self.lonFld = self._field(210, y, 170, "经度 104.0300")
        c.addSubview_(self.latFld)
        c.addSubview_(self.lonFld)

        # 默认值
        self.latFld.setStringValue_("30.4799")
        self.lonFld.setStringValue_("104.0300")
        y -= 35

        # 设定 + 重置
        setBtn = self._btn("📍 设定位置", 20, y, 180, self.onSet_)
        rstBtn = self._btn("🔄 重置定位", 220, y, 180, self.onReset_)
        c.addSubview_(setBtn)
        c.addSubview_(rstBtn)
        y -= 35

        # 启动 + 关闭
        startBtn = self._btn("🟢 启动隧道", 20, y, 180, self.onStart_)
        stopBtn = self._btn("🔴 关闭隧道", 220, y, 180, self.onStop_)
        c.addSubview_(startBtn)
        c.addSubview_(stopBtn)

        self.win.makeKeyAndOrderFront_(None)
        self._checkDevice()

    @objc.python_method
    def _lbl(self, text, size=13, color=None):
        lbl = NSTextField.labelWithString_(text)
        lbl.setFont_(NSFont.systemFontOfSize_(size))
        if color:
            lbl.setTextColor_(color)
        return lbl

    @objc.python_method
    def _lbl_at(self, text, size, bold, x, y):
        lbl = NSTextField.labelWithString_(text)
        if bold:
            lbl.setFont_(NSFont.boldSystemFontOfSize_(size))
        else:
            lbl.setFont_(NSFont.systemFontOfSize_(size))
        lbl.setFrame_(NSMakeRect(x, y, 380, 20))
        return lbl

    @objc.python_method
    def _field(self, x, y, w, placeholder):
        f = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, w, 24))
        f.setPlaceholderString_(placeholder)
        f.setFont_(NSFont.monospacedSystemFontOfSize_weight_(13, 0))
        return f

    @objc.python_method
    def _btn(self, title, x, y, w, action):
        b = NSButton.alloc().initWithFrame_(NSMakeRect(x, y, w, 28))
        b.setTitle_(title)
        b.setBezelStyle_(NSBezelStyleRounded)
        b.setTarget_(self)
        b.setAction_(action)
        b.setFont_(NSFont.systemFontOfSize_(13))
        return b

    @objc.python_method
    def _sep(self, y):
        from AppKit import NSBox
        box = NSBox.alloc().initWithFrame_(NSMakeRect(20, y, 380, 1))
        box.setBoxType_(2)
        return box

    @objc.python_method
    def _setStatus(self, text):
        self.statusLbl.performSelectorOnMainThread_withObject_waitUntilDone_(
            "setStringValue:", text, False
        )

    @objc.python_method
    def _askPassword(self):
        """弹出对话框获取 Mac 密码"""
        r = subprocess.run([
            "osascript", "-e",
            'display dialog "输入 Mac 密码（sudo 启动隧道）:" default answer "" '
            'with hidden answer with title "fakeloc" buttons {"取消","确定"} '
            'default button "确定"'
        ], capture_output=True, text=True)
        if r.returncode != 0:
            return None
        for part in r.stdout.strip().split(","):
            if "text returned:" in part:
                return part.split("text returned:")[1].strip()
        return None

    @objc.python_method
    def _checkDevice(self):
        def _do():
            try:
                r = subprocess.run([PMD3, "usbmux", "list"],
                                   capture_output=True, text=True, timeout=5)
                if "ProductType" in r.stdout:
                    self._setStatus("📱 iPhone 已连接 · 就绪")
                else:
                    self._setStatus("⚠️ 未检测到 iPhone")
            except Exception:
                self._setStatus("⚠️ pymobiledevice3 未找到")
        threading.Thread(target=_do, daemon=True).start()

    def presetClicked_(self, sender):
        tag = sender.tag()
        if tag in self.presetBtns:
            lat, lon = self.presetBtns[tag]
            self.latFld.setStringValue_(lat)
            self.lonFld.setStringValue_(lon)

    def onStart_(self, sender):
        global rsd_addr, rsd_port
        if self.isRunning:
            self._setStatus("隧道已在运行中")
            return
        # 弹密码框（主线程）
        r = subprocess.run([
            "osascript", "-e",
            'display dialog "输入 Mac 密码（sudo 启动隧道）:" default answer "" '
            'with hidden answer with title "fakeloc" buttons {"取消","确定"} '
            'default button "确定"'
        ], capture_output=True, text=True)
        if r.returncode != 0:
            self._setStatus("已取消")
            return
        password = None
        for part in r.stdout.strip().split(","):
            if "text returned:" in part:
                password = part.split("text returned:")[1].strip()
        if not password:
            self._setStatus("未输入密码")
            return

        # 写入临时文件给 askpass 读取
        with open("/tmp/.fakeloc_pw", "w") as f:
            f.write(password)
        os.chmod("/tmp/.fakeloc_pw", 0o600)

        # 杀旧隧道
        subprocess.run(["pkill", "-f", "start-tunnel"], capture_output=True)
        self._setStatus("正在启动隧道...")
        self.isRunning = False

        def _do():
            global rsd_addr, rsd_port
            env = os.environ.copy()
            env["SUDO_ASKPASS"] = os.path.expanduser("~/.local/bin/fakeloc-askpass")
            try:
                proc = subprocess.Popen(
                    ["sudo", "-A", PMD3, "remote", "start-tunnel",
                     "--script-mode", "-t", "usb"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, env=env
                )
                # 逐行读取 stdout
                for i in range(30):
                    ready, _, _ = select.select([proc.stdout], [], [], 1)
                    if ready:
                        line = proc.stdout.readline()
                        if not line:
                            break
                        line = line.strip()
                        # script-mode 输出格式: [addr]:port 或 addr port
                        if "[" in line and "]" in line:
                            idx = line.index("]")
                            addr = line[:idx+1]
                            port = int(line[idx+2:].split()[0])
                            rsd_addr, rsd_port = addr, port
                            self.isRunning = True
                            self._setStatus(f"✅ 隧道运行中  {rsd_addr}:{rsd_port}")
                            return
                        elif line and " " in line:
                            parts = line.split()
                            if len(parts) >= 2:
                                try:
                                    port = int(parts[-1])
                                    addr = parts[0]
                                    rsd_addr, rsd_port = addr, port
                                    self.isRunning = True
                                    self._setStatus(f"✅ 隧道运行中  {rsd_addr}:{rsd_port}")
                                    return
                                except ValueError:
                                    pass
                    if proc.poll() is not None:
                        err = proc.stderr.read() or ""
                        self._setStatus(f"❌ 失败: {err.strip()[:120]}")
                        return
                # 读取 stderr 看是否有错误
                proc.kill()
                err = proc.stderr.read() or ""
                if err.strip():
                    self._setStatus(f"❌ {err.strip()[:120]}")
                else:
                    self._setStatus("❌ 超时，未收到地址")
            except Exception as e:
                self._setStatus(f"❌ {e}")
            finally:
                # 清理密码文件
                try: os.unlink("/tmp/.fakeloc_pw")
                except: pass
        threading.Thread(target=_do, daemon=True).start()

    def onStop_(self, sender):
        global keep_alive
        keep_alive = False
        subprocess.run(["pkill", "-f", "start-tunnel"], capture_output=True)
        global rsd_addr, rsd_port
        rsd_addr, rsd_port = None, None
        self.isRunning = False
        self._setStatus("🔴 隧道已关闭")

    def onSet_(self, sender):
        global rsd_addr, rsd_port, keep_alive
        lat = self.latFld.stringValue().strip()
        lon = self.lonFld.stringValue().strip()
        if not lat or not lon:
            self._setStatus("⚠️ 请输入坐标")
            return
        if not rsd_addr:
            self._setStatus("⚠️ 请先启动隧道")
            return
        keep_alive = True
        self._setStatus(f"📍 定位中: {lat}, {lon}（持续保持）")
        def _do():
            global keep_alive
            first = True
            while keep_alive and rsd_addr:
                try:
                    r = subprocess.run(
                        [PMD3, "developer", "dvt", "simulate-location", "set",
                         "--rsd", rsd_addr, str(rsd_port), "--", lat, lon],
                        capture_output=True, text=True, timeout=10
                    )
                    if first:
                        if r.returncode == 0:
                            self._setStatus(f"✅ 定位保持中: {lat}, {lon}")
                        else:
                            self._setStatus(f"❌ 失败: {(r.stderr or '')[:100]}")
                            keep_alive = False
                            return
                        first = False
                except Exception:
                    pass
                # 每 1 秒发一次（减少真实 GPS 闪回）
                for _ in range(10):
                    if not keep_alive:
                        return
                    import time; time.sleep(0.1)
        threading.Thread(target=_do, daemon=True).start()

    def onReset_(self, sender):
        global rsd_addr, rsd_port, keep_alive
        keep_alive = False
        if not rsd_addr:
            self._setStatus("⚠️ 请先启动隧道")
            return
        def _do():
            try:
                r = subprocess.run(
                    [PMD3, "developer", "dvt", "simulate-location", "clear",
                     "--rsd", rsd_addr, str(rsd_port)],
                    capture_output=True, text=True, timeout=10
                )
                if r.returncode == 0:
                    self._setStatus("✅ 定位已重置")
                else:
                    self._setStatus("❌ 重置失败")
            except Exception as e:
                self._setStatus(f"❌ {e}")
        threading.Thread(target=_do, daemon=True).start()


def main():
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    delegate = App.alloc().init()
    app.setDelegate_(delegate)
    app.activateIgnoringOtherApps_(True)
    app.run()

if __name__ == "__main__":
    main()
