
import psutil
import win32gui
import win32process

def shouldShowOverlay(self):
    hwnd = win32gui.GetForegroundWindow()
    pid = None
    if hwnd:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

    current_process = None
    if pid:
        try:
            current_process = psutil.Process(pid).name()
        except psutil.NoSuchProcess:
            pass

    process = self.process
    should_show = self.active and (process == "All" or process == current_process)

    if should_show and not self.isVisible():  
        self.show()
    elif not should_show and self.isVisible():  
        self.hide()