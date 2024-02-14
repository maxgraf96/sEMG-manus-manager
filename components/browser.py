import tkinter as tk
from tkinter import *
from cefpython3 import cefpython as cef
import ctypes

from cefpython3.examples.tkinter_ import WINDOWS


class BrowserFrame(tk.Frame):

    def __init__(self, mainframe):
        self.should_close = False
        self.closing = False
        self.browser = None
        tk.Frame.__init__(self, mainframe)
        self.mainframe = mainframe
        self.bind("<FocusIn>", self.on_focus_in)
        self.bind("<FocusOut>", self.on_focus_out)
        self.bind("<Configure>", self.on_configure)
        """For focus problems see Issue #255 and Issue #535. """
        self.focus_set()

    # URLURLURL
    def embed_browser(self, url):
        window_info = cef.WindowInfo()
        # rect = [0, 0, self.winfo_width(), self.winfo_height()]
        rect = [0, 0, 800, 600]
        window_info.SetAsChild(self.get_window_handle(), rect)
        self.browser = cef.CreateBrowserSync(window_info, url=url)
        assert self.browser
        self.browser.SetClientHandler(LifespanHandler(self))
        self.browser.SetClientHandler(LoadHandler(self))
        self.browser.SetClientHandler(FocusHandler(self))
        self.message_loop_work()

    def reload_page(self):
        self.browser.Reload()

    def get_window_handle(self):
        if self.winfo_id() > 0:
            return self.winfo_id()
        else:
            raise Exception("Couldn't obtain window handle")

    def message_loop_work(self):
        if self.should_close:
            return
        cef.MessageLoopWork()
        self.after(10, self.message_loop_work)

    def on_configure(self, url):
        if not self.browser:
            self.embed_browser(url)

    def on_root_configure(self):
        # Root <Configure> event will be called when top window is moved
        if self.browser:
            self.browser.NotifyMoveOrResizeStarted()

    def on_mainframe_configure(self, width, height):
        if self.browser:
            if WINDOWS:
                ctypes.windll.user32.SetWindowPos(
                    self.browser.GetWindowHandle(), 0,
                    0, 0, width, height, 0x0002)
            self.browser.NotifyMoveOrResizeStarted()

    def on_focus_in(self, _):
        # logger.debug("BrowserFrame.on_focus_in")
        if self.browser:
            self.browser.SetFocus(True)

    def on_focus_out(self, _):
        # logger.debug("BrowserFrame.on_focus_out")
        """For focus problems see Issue #255 and Issue #535. """
        pass

    def on_root_close(self):
        self.should_close = True
        if self.browser:
            self.browser.CloseBrowser(True)
            self.clear_browser_references()
        else:
            self.destroy()


    def clear_browser_references(self):
        # Clear browser references that you keep anywhere in your
        # code. All references must be cleared for CEF to shutdown cleanly.
        self.browser = None


class LifespanHandler(object):

    def __init__(self, tkFrame):
        self.tkFrame = tkFrame

    def OnBeforeClose(self, browser, **_):
        # logger.debug("LifespanHandler.OnBeforeClose")
        self.tkFrame.destroy()
        pass


class LoadHandler(object):

    def __init__(self, browser_frame):
        self.browser_frame = browser_frame

    def OnLoadStart(self, browser, **_):
        pass
        # if self.browser_frame.master.navigation_bar:
        #     self.browser_frame.master.navigation_bar.set_url(browser.GetUrl())


class FocusHandler(object):
    """For focus problems see Issue #255 and Issue #535. """

    def __init__(self, browser_frame):
        self.browser_frame = browser_frame

    def OnTakeFocus(self, next_component, **_):
        pass  # logger.debug("FocusHandler.OnTakeFocus, next={next}".format(next=next_component))

    def OnSetFocus(self, source, **_):
        return True

    def OnGotFocus(self, **_):
        # logger.debug("FocusHandler.OnGotFocus")
        pass
