import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import pygame, os, sys

APP_TITLE = "calc"
IMG_BG = "EN.png"
IMG_CALL = "caller.png"
IMG_PICK = "pick.png"
IMG_HANG = "hang.png"
MUSIC_IDLE = "music.mp3"
MUSIC_CALL = "call.mp3"
SFX_PICK = "ty.mp3"
WINDOW_MIN_W = 360
WINDOW_MIN_H = 540


def resource_path(name):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, name)


class StretchBG:
    def __init__(self, parent, path):
        self.parent = parent
        self.path = resource_path(path)
        try:
            self.img = Image.open(self.path).convert("RGBA")
        except:
            self.img = Image.new("RGBA", (100, 100), "gray")
        self.tk_img = None
        self.label = tk.Label(parent, bd=0)
        self.label.place(x=0, y=0, relwidth=1, relheight=1)
        self.parent.bind("<Configure>", self.resize)
        self.resize()

    def resize(self, event=None):
        w = self.parent.winfo_width()
        h = self.parent.winfo_height()
        if w < 5 or h < 5:
            return
        resized = self.img.resize((w, h), Image.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(resized)
        self.label.config(image=self.tk_img)


class CalcApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.minsize(WINDOW_MIN_W, WINDOW_MIN_H)

        pygame.mixer.init()
        try:
            self.pick_sound = pygame.mixer.Sound(resource_path(SFX_PICK))
        except:
            self.pick_sound = None

        self.pending_expr = None
        self.on_call_screen = False

        # fő frame
        self.main_frame = tk.Frame(self, bg="#000")
        self.main_frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.bg_main = StretchBG(self.main_frame, IMG_BG)

        self.display_var = tk.StringVar(value="")
        self.display = ttk.Entry(
            self.main_frame, textvariable=self.display_var, font=("JetBrains Mono", 18)
        )
        self.display.place(relx=0.05, rely=0.06, relwidth=0.9, height=48)
        self._build_keypad()

        # hívás frame
        self.call_frame = tk.Frame(self, bg="#000")
        # háttér külön labelen, hogy biztos látszódjon
        self.call_bg_label = tk.Label(self.call_frame, bd=0)
        self.call_bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.call_bg = None

        self.call_label = tk.Label(
            self.call_frame,
            text="INCOMING CALL 📞",
            font=("Arial Black", 26, "bold"),
            fg="lime",
            bg="black",
        )
        self.call_label.place(relx=0.1, rely=0.05, relwidth=0.8)
        self._blink_on = True
        self.after(500, self._blink_label)

        self.pick_raw = Image.open(resource_path(IMG_PICK)).convert("RGBA")
        self.hang_raw = Image.open(resource_path(IMG_HANG)).convert("RGBA")
        self.pick_img = ImageTk.PhotoImage(self.pick_raw)
        self.hang_img = ImageTk.PhotoImage(self.hang_raw)
        self.pick_btn = tk.Button(
            self.call_frame, bd=0, highlightthickness=0, command=self.on_pick
        )
        self.hang_btn = tk.Button(
            self.call_frame, bd=0, highlightthickness=0, command=self.on_hang
        )
        self.pick_btn.place(x=60, rely=0.8, width=120, height=80)
        self.hang_btn.place(x=240, rely=0.8, width=120, height=80)
        self.call_frame.bind("<Configure>", self._resize_call_elements)

        self.play_idle_music()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # -------- villogó szöveg --------
    def _blink_label(self):
        if self.on_call_screen:
            self.call_label.config(fg="lime" if self._blink_on else "black")
            self._blink_on = not self._blink_on
        self.after(500, self._blink_label)

    # -------- zene --------
    def play_idle_music(self):
        try:
            pygame.mixer.music.load(resource_path(MUSIC_IDLE))
            pygame.mixer.music.play(-1)
        except:
            pass

    def play_call_music(self):
        try:
            pygame.mixer.music.load(resource_path(MUSIC_CALL))
            pygame.mixer.music.play(-1)
        except:
            pass

    def stop_music(self):
        try:
            pygame.mixer.music.stop()
        except:
            pass

    def play_pick_sfx(self):
        if self.pick_sound:
            try:
                self.pick_sound.play()
            except:
                pass

    # -------- hívásképernyő frissítés --------
    def _resize_call_elements(self, event=None):
        # háttér
        w = self.call_frame.winfo_width()
        h = self.call_frame.winfo_height()
        try:
            bg = Image.open(resource_path(IMG_CALL)).convert("RGBA").resize((w, h), Image.LANCZOS)
            self.call_bg = ImageTk.PhotoImage(bg)
            self.call_bg_label.config(image=self.call_bg)
        except:
            pass
        # gombképek
        for raw, attr, btn in [
            (self.pick_raw, "pick_img", self.pick_btn),
            (self.hang_raw, "hang_img", self.hang_btn),
        ]:
            bw, bh = btn.winfo_width(), btn.winfo_height()
            if bw > 2 and bh > 2:
                im = raw.resize((bw, bh), Image.NEAREST)
                tkimg = ImageTk.PhotoImage(im)
                setattr(self, attr, tkimg)
                btn.config(image=tkimg)

    # -------- keypad --------
    def _build_keypad(self):
        keys = [
            ["7", "8", "9", "/"],
            ["4", "5", "6", "*"],
            ["1", "2", "3", "-"],
            ["(", "0", ")", "+"],
            ["C", "Del", ".", "="],
        ]
        base_y = 0.16
        row_h = 0.14
        col_w = 0.21
        gap_x = 0.04
        gap_y = 0.02
        start_x = 0.05
        for r, row in enumerate(keys):
            for c, key in enumerate(row):
                btn = ttk.Button(
                    self.main_frame, text=key, command=lambda k=key: self.on_key(k)
                )
                x = start_x + c * (col_w + gap_x)
                y = base_y + r * (row_h + gap_y)
                btn.place(relx=x, rely=y, relwidth=col_w, relheight=row_h)

    # -------- logika --------
    def on_key(self, k):
        if k == "C":
            self.display_var.set("")
        elif k == "Del":
            cur = self.display_var.get()
            self.display_var.set(cur[:-1])
        elif k == "=":
            expr = self.display_var.get().strip()
            if expr:
                self.pending_expr = expr
                self.show_call_screen()
        else:
            self.display_var.set(self.display_var.get() + k)

    def show_call_screen(self):
        if self.on_call_screen:
            return
        self.on_call_screen = True
        self.stop_music()
        self.play_call_music()
        self.call_frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.call_frame.tkraise()
        self._resize_call_elements()

    def hide_call_screen(self):
        self.on_call_screen = False
        self.call_frame.place_forget()

    def on_pick(self):
        self.stop_music()
        self.play_pick_sfx()
        self.hide_call_screen()
        self.show_result_after_call()
        self.play_idle_music()

    def on_hang(self):
        self.stop_music()
        self.destroy()

    def show_result_after_call(self):
        expr = self.pending_expr or ""
        self.pending_expr = None
        try:
            result = eval(expr, {"__builtins__": {}}, {})
        except Exception:
            result = "Error"
        self.display_var.set(f"{expr} = {result}")

    def _on_close(self):
        self.stop_music()
        self.destroy()


if __name__ == "__main__":
    app = CalcApp()
    app.mainloop()
