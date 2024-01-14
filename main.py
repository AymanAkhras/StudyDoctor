from datetime import datetime
from typing import Any, Tuple
from tkinter import IntVar
import tkinter as tk
import customtkinter
from win32gui import GetForegroundWindow
import win32process
import psutil
import threading
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk as NavigationToolbar2TkAgg,
)

from app.facereader import FaceReader
from utils import start_study_session

matplotlib.use("TkAgg")


class App(customtkinter.CTk):
    VALID_APPS = ["chrome", "code"]
    APP_TITLE = "Study Doctor"
    APP_SCREEN_SIZE = "400x400"

    def __init__(
        self, fg_color: str | Tuple[str, str] | None = None, **kwargs
    ):
        super().__init__(fg_color, **kwargs)
        self.title(self.APP_TITLE)
        self.geometry(self.APP_SCREEN_SIZE)
        self.tabview = Tabs(master=self)
        self.tabview.pack()


class Help(customtkinter.CTkToplevel):
    SCREEN_TITLE = "Help - Study Doctor"
    APP_SCREEN_SIZE = "400x400"

    def __init__(
        self, *args, fg_color: str | Tuple[str, str] | None = None, **kwargs
    ):
        super().__init__(*args, fg_color=fg_color, **kwargs)
        self.after(0, self.lift)
        self.title(self.SCREEN_TITLE)
        self.geometry(self.APP_SCREEN_SIZE)
        self.label = customtkinter.CTkLabel(self, text="Help")
        self.label.pack()
        self.close_button = customtkinter.CTkButton(
            self, text="Close", command=self.onclick_close
        )
        self.close_button.pack()

    def onclick_close(self):
        self.destroy()


class Tabs(customtkinter.CTkTabview):
    def __init__(
        self,
        master: Any,
    ):
        super().__init__(
            master,
        )

        self.add("Main")
        self.add("Timer")
        self.add("Review")
        self.main_screen = MainScreen(master=self.tab("Main"))
        self.main_screen.pack()
        self.timer_screen = TimerScreen(master=self.tab("Timer"))
        self.timer_screen.pack()
        self.review_screen = ReviewScreen(master=self.tab("Review"))
        self.review_screen.pack()


class MainScreen(customtkinter.CTkFrame):
    VALID_APPS = ["chrome", "code"]

    def __init__(
        self,
        master: Any,
    ):
        super().__init__(
            master,
        )
        self.label = customtkinter.CTkLabel(self, text="")
        self.label.pack()
        self.get_current_app()
        self.session_count = IntVar(value=1)
        self.timer_count = IntVar(value=20)
        self.timer_count_label = customtkinter.CTkLabel(
            self, text=f"Timer: {self.timer_count.get()} mins"
        )
        self.timer_count_label.pack()
        self.timer_slider = customtkinter.CTkSlider(
            self,
            from_=15,
            to=35,
            variable=self.timer_count,
            number_of_steps=20,
            command=self.onchange_timer_slider,
        )
        self.timer_slider.pack()
        self.session_count_label = customtkinter.CTkLabel(
            self, text=f"Session Count: {self.session_count.get()}"
        )
        self.session_count_label.pack()
        self.session_slider = customtkinter.CTkSlider(
            self,
            from_=1,
            to=10,
            variable=self.session_count,
            number_of_steps=9,
            command=self.onchange_session_slider,
        )
        self.session_slider.pack()
        self.start_button = customtkinter.CTkButton(
            self, text="Start", command=self.onclick_start
        )
        self.start_button.pack()
        self.help_button = customtkinter.CTkButton(
            self, text="Help", command=self.onclick_help
        )
        self.help_button.pack()
        self.help_window = None
        self.face_reader = FaceReader()

        self.t = threading.Thread(
            target=self.face_reader.setup,
        )
        self.t.start()
        # self.face_reader.setup()

    def onchange_timer_slider(self, value):
        self.timer_count.set(value)
        self.timer_count_label.configure(
            text=f"Timer: {self.timer_count.get()} mins"
        )

    def onchange_session_slider(self, value):
        self.session_count.set(value)
        self.session_count_label.configure(
            text=f"Session Count: {self.session_count.get()}"
        )

    def get_current_app(self):
        # pid = win32process.GetWindowThreadProcessId(GetForegroundWindow())
        # process_name = psutil.Process(pid[-1]).name().split(".")[0].lower()

        # if process_name in self.VALID_APPS:
        #     self.label.configure(text=process_name)
        # else:
        #     self.label.configure(text="DO YOUR WORK!")
        self.after(2000, self.get_current_app)

    def onclick_start(self):
        duration = self.timer_count.get()
        start_study_session(
            duration=duration, func=self.face_reader.data_collection
        )

        app.tabview.set("Timer")
        self.master.master.timer_screen.start()

    def onclick_help(self):
        if self.help_window is None or not self.help_window.winfo_exists():
            self.help_window = Help(
                self
            )  # create window if its None or destroyed
            self.help_window.after(10, self.help_window.lift)
        else:
            self.help_window.focus()  # if window exists focus it


class TimerScreen(customtkinter.CTkFrame):
    def __init__(
        self,
        master: Any,
    ):
        super().__init__(
            master,
        )
        self.session_label = customtkinter.CTkLabel(self, text="")
        self.session_label.pack()
        self.timer_label = customtkinter.CTkLabel(
            self, text="Start a session!"
        )
        self.timer_label.pack()
        self.func = self.master.master.main_screen.face_reader.data_collection

    def start(self):
        self.total_sessions = int(
            self.master.master.main_screen.session_count.get()
        )
        self.curr_session = 1
        self.time_per_session = (
            self.master.master.main_screen.timer_count.get()
        )
        self.curr_session_type = 1  # 1 is study, 0 is break

        self.start_timer(time_left=self.time_per_session)

    def start_timer(self, time_left: int):
        self.time_left = time_left
        self.update()

    def update(self):
        if self.time_left >= 0:
            sessions_left_text = f"Session {self.curr_session}/{self.total_sessions} - {'study' if self.curr_session_type == 1 else 'break'}"
            self.session_label.configure(text=sessions_left_text)
            timer_label_text = (
                f"Time left: {self.time_left//60}:{self.time_left%60}"
            )
            self.timer_label.configure(text=timer_label_text)
            self.time_left -= 1
            self.after(1000, self.update)
        else:
            if self.curr_session_type == 1:
                self.curr_session_type = 0
                self.start_timer(time_left=5)  # 5 min
            else:
                self.curr_session_type = 1
                self.curr_session += 1
                if self.curr_session <= self.total_sessions:
                    start_study_session(
                        duration=self.time_per_session, func=self.func
                    )
                    self.start_timer(time_left=self.time_per_session)

                else:
                    self.timer_label.configure(
                        text="Congrats, you're all done! :D"
                    )


class ReviewScreen(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.refresh_button = customtkinter.CTkButton(
            self, text="Refresh", command=self.update
        )
        self.refresh_button.pack()
        self.update()

    def update(self):
        with open("./logs/logs.txt") as f:
            prev = f.readlines()[-1].strip()

        with open(f"./logs/{prev}.csv") as f:
            next(f)
            inputs = [(line.strip().split(",")) for line in f]

        self.label = customtkinter.CTkLabel(self, text=prev)
        self.label.pack()

        x = [float(line[0]) for line in inputs]
        distracted_time = [float(line[1]) for line in inputs]
        blink_ct = [float(line[2]) for line in inputs]
        yawn_ct = [float(line[3]) for line in inputs]

        f = Figure(figsize=(8, 8), dpi=100)
        a = f.add_subplot(221)
        a.title.set_text("Distracted time")
        a.plot(x, distracted_time)
        b = f.add_subplot(222)
        b.plot(x, blink_ct)
        b.title.set_text("Blink count")
        c = f.add_subplot(223)
        c.plot(x, yawn_ct)
        c.title.set_text("Yawn count")

        canvas = FigureCanvasTkAgg(f, self)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)


app = App()
app.mainloop()
