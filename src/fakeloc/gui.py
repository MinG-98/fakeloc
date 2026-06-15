#!/usr/bin/env python3
"""fakeloc GUI — macOS native window for iPhone GPS spoofing."""

import os
import subprocess
import threading
import time

import objc
from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSBackingStoreBuffered,
    NSBezelStyleRounded,
    NSBox,
    NSButton,
    NSColor,
    NSFont,
    NSMakeRect,
    NSRunLoop,
    NSDate,
    NSTextField,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskTitled,
)
from Foundation import NSObject

from fakeloc.core import (
    GUI_PRESETS,
    _pmd3_path,
    get_tunnel,
    save_tunnel,
    start_tunnel_with_askpass,
)


# Module-level mutable state used by the GUI
rsd_addr: str | None = None
rsd_port: str | None = None
keep_alive: bool = False


class FakelocApp(NSObject):
    """Main GUI application controller."""

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
            NSBackingStoreBuffered,
            False,
        )
        self.win.setTitle_("📍 fakeloc - iPhone GPS Spoofing")
        self.win.setLevel_(3)

        c = self.win.contentView()
        y = 380

        # Status label
        self.statusLbl = self._lbl("Detecting device...", 12, NSColor.secondaryLabelColor())
        self.statusLbl.setFrame_(NSMakeRect(20, y, 380, 20))
        c.addSubview_(self.statusLbl)
        y -= 30

        # Separator
        c.addSubview_(self._sep(y))
        y -= 20

        # Preset locations
        c.addSubview_(self._lbl_at("Preset Locations", 14, True, 20, y))
        y -= 30

        for name, (lat, lon) in GUI_PRESETS.items():
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

        # Coordinate input
        c.addSubview_(self._lbl_at("Coordinates (WGS-84)", 14, True, 20, y))
        y -= 28

        self.latFld = self._field(20, y, 170, "Latitude 30.4799")
        self.lonFld = self._field(210, y, 170, "Longitude 104.0300")
        c.addSubview_(self.latFld)
        c.addSubview_(self.lonFld)

        # Default values
        self.latFld.setStringValue_("30.4799")
        self.lonFld.setStringValue_("104.0300")
        y -= 35

        # Set + Reset buttons
        setBtn = self._btn("📍 Set Location", 20, y, 180, self.onSet_)
        rstBtn = self._btn("🔄 Reset Location", 220, y, 180, self.onReset_)
        c.addSubview_(setBtn)
        c.addSubview_(rstBtn)
        y -= 35

        # Start + Stop tunnel buttons
        startBtn = self._btn("🟢 Start Tunnel", 20, y, 180, self.onStart_)
        stopBtn = self._btn("🔴 Stop Tunnel", 220, y, 180, self.onStop_)
        c.addSubview_(startBtn)
        c.addSubview_(stopBtn)

        self.win.makeKeyAndOrderFront_(None)
        self._checkDevice()

    # ── UI helpers ───────────────────────────────────────────────────────────

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
        """Show a dialog to get the Mac password."""
        r = subprocess.run(
            [
                "osascript", "-e",
                'display dialog "Enter Mac password (for sudo tunnel):" default answer "" '
                'with hidden answer with title "fakeloc" buttons {"Cancel","OK"} '
                'default button "OK"',
            ],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            return None
        for part in r.stdout.strip().split(","):
            if "text returned:" in part:
                return part.split("text returned:")[1].strip()
        return None

    @objc.python_method
    def _checkDevice(self):
        def _do():
            pmd3 = _pmd3_path()
            try:
                r = subprocess.run(
                    [pmd3, "usbmux", "list"],
                    capture_output=True, text=True, timeout=5,
                )
                if "ProductType" in r.stdout:
                    self._setStatus("📱 iPhone connected · ready")
                else:
                    self._setStatus("⚠️ No iPhone detected")
            except Exception:
                self._setStatus("⚠️ pymobiledevice3 not found")

        threading.Thread(target=_do, daemon=True).start()

    # ── Button actions ───────────────────────────────────────────────────────

    def presetClicked_(self, sender):
        tag = sender.tag()
        if tag in self.presetBtns:
            lat, lon = self.presetBtns[tag]
            self.latFld.setStringValue_(lat)
            self.lonFld.setStringValue_(lon)

    def onStart_(self, sender):
        global rsd_addr, rsd_port
        if self.isRunning:
            self._setStatus("Tunnel already running")
            return

        # Prompt for password
        r = subprocess.run(
            [
                "osascript", "-e",
                'display dialog "Enter Mac password (for sudo tunnel):" default answer "" '
                'with hidden answer with title "fakeloc" buttons {"Cancel","OK"} '
                'default button "OK"',
            ],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            self._setStatus("Cancelled")
            return
        password = None
        for part in r.stdout.strip().split(","):
            if "text returned:" in part:
                password = part.split("text returned:")[1].strip()
        if not password:
            self._setStatus("No password entered")
            return

        self._setStatus("Starting tunnel...")
        self.isRunning = False

        def _do():
            global rsd_addr, rsd_port
            ok, msg = start_tunnel_with_askpass(password)
            if ok:
                # msg is "addr:port" format — parse for display
                if ":" in msg:
                    parts = msg.rsplit(":", 1)
                    rsd_addr, rsd_port = parts[0], parts[1]
                else:
                    rsd_addr, rsd_port = msg, ""
                self.isRunning = True
                self._setStatus(f"✅ Tunnel running  {rsd_addr}:{rsd_port}")
            else:
                self._setStatus(f"❌ {msg}")

        threading.Thread(target=_do, daemon=True).start()

    def onStop_(self, sender):
        global keep_alive, rsd_addr, rsd_port
        keep_alive = False
        subprocess.run(["pkill", "-f", "start-tunnel"], capture_output=True)
        rsd_addr, rsd_port = None, None
        self.isRunning = False
        self._setStatus("🔴 Tunnel stopped")

    def onSet_(self, sender):
        global rsd_addr, rsd_port, keep_alive
        lat = self.latFld.stringValue().strip()
        lon = self.lonFld.stringValue().strip()
        if not lat or not lon:
            self._setStatus("⚠️ Please enter coordinates")
            return
        if not rsd_addr:
            self._setStatus("⚠️ Start the tunnel first")
            return

        keep_alive = True
        self._setStatus(f"📍 Locating: {lat}, {lon} (keeping alive)")

        def _do():
            global keep_alive
            pmd3 = _pmd3_path()
            first = True
            while keep_alive and rsd_addr:
                try:
                    r = subprocess.run(
                        [pmd3, "developer", "dvt", "simulate-location", "set",
                         "--rsd", rsd_addr, str(rsd_port), "--", lat, lon],
                        capture_output=True, text=True, timeout=10,
                    )
                    if first:
                        if r.returncode == 0:
                            self._setStatus(f"✅ Location held: {lat}, {lon}")
                        else:
                            self._setStatus(f"❌ Failed: {(r.stderr or '')[:100]}")
                            keep_alive = False
                            return
                        first = False
                except Exception:
                    pass
                # Resend every 1 second (prevents real GPS flash-back)
                for _ in range(10):
                    if not keep_alive:
                        return
                    time.sleep(0.1)

        threading.Thread(target=_do, daemon=True).start()

    def onReset_(self, sender):
        global rsd_addr, rsd_port, keep_alive
        keep_alive = False
        if not rsd_addr:
            self._setStatus("⚠️ Start the tunnel first")
            return

        def _do():
            pmd3 = _pmd3_path()
            try:
                r = subprocess.run(
                    [pmd3, "developer", "dvt", "simulate-location", "clear",
                     "--rsd", rsd_addr, str(rsd_port)],
                    capture_output=True, text=True, timeout=10,
                )
                if r.returncode == 0:
                    self._setStatus("✅ Location reset")
                else:
                    self._setStatus("❌ Reset failed")
            except Exception as e:
                self._setStatus(f"❌ {e}")

        threading.Thread(target=_do, daemon=True).start()


def main():
    """Entry point for the GUI application."""
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    delegate = FakelocApp.alloc().init()
    app.setDelegate_(delegate)
    app.activateIgnoringOtherApps_(True)
    app.run()


if __name__ == "__main__":
    main()
