#!/usr/bin/env python3
"""
Windows service wrapper for GlanceRF headless (server-only) mode.
Install: python glancerf/desktop/glancerf_service.py install (requires Administrator)
"""

import os
import sys
import subprocess
import time

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)


def _run_py():
    exe = sys.executable
    if exe.lower().endswith("pythonservice.exe"):
        exe = os.path.join(os.path.dirname(exe), "python.exe")
    return exe


class GlanceRFService:
    """Runs run.py in a subprocess; stops it when the service stops."""

    def __init__(self):
        self.process = None
        self.running = False

    def run(self):
        self.running = True
        run_py = os.path.join(PROJECT_DIR, "run.py")
        env = os.environ.copy()
        env["GLANCERF_PROJECT"] = PROJECT_DIR
        log_path = os.path.join(PROJECT_DIR, "glancerf_service.log")
        try:
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write("\n--- service start %s ---\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
                log_file.flush()
                self.process = subprocess.Popen(
                    [_run_py(), run_py],
                    cwd=PROJECT_DIR,
                    env=env,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                )
                while self.running and self.process.poll() is None:
                    time.sleep(1)
                exit_code = self.process.poll()
                if exit_code is not None:
                    log_file.write("--- process exited with code %s ---\n" % exit_code)
                if self.process.poll() is None:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
        except Exception as e:
            try:
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.write("--- service exception: %s ---\n" % e)
            except Exception:
                pass
            if self.process and self.process.poll() is None:
                self.process.terminate()
            raise

    def stop(self):
        self.running = False
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()


try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
except ImportError:
    print("pywin32 is required for the GlanceRF Windows service. Install with: pip install pywin32")
    sys.exit(1)


class GlanceRFServiceFramework(win32serviceutil.ServiceFramework):
    _svc_name_ = "GlanceRF"
    _svc_display_name_ = "GlanceRF"
    _svc_description_ = "GlanceRF dashboard (headless web server)"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.impl = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.impl:
            self.impl.stop()
        win32event.SetEvent(self.stop_event)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        self.impl = GlanceRFService()
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        self.impl.run()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(GlanceRFServiceFramework)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(GlanceRFServiceFramework)
