import os, shutil, subprocess, time
os.environ["TK_SILENCE_DEPRECATION"] = "1"
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime

# ═══════════════════════════════════════════════════
#  THEME  — Catppuccin Mocha dark palette
# ═══════════════════════════════════════════════════
C = {
    "base":     "#1e1e2e",
    "mantle":   "#181825",
    "crust":    "#11111b",
    "surface0": "#313244",
    "surface1": "#45475a",
    "surface2": "#585b70",
    "overlay0": "#6c7086",
    "overlay1": "#7f849c",
    "text":     "#cdd6f4",
    "subtext":  "#a6adc8",
    "blue":     "#89b4fa",
    "lavender": "#b4befe",
    "sapphire": "#74c7ec",
    "sky":      "#89dceb",
    "teal":     "#94e2d5",
    "green":    "#a6e3a1",
    "yellow":   "#f9e2af",
    "peach":    "#fab387",
    "red":      "#f38ba8",
    "mauve":    "#cba6f7",
    "pink":     "#f5c2e7",
}

FONT_UI   = ("Helvetica Neue", 13)
FONT_MONO = ("Menlo", 12)
FONT_SM   = ("Helvetica Neue", 11)
FONT_LG   = ("Helvetica Neue", 15, "bold")
FONT_XS   = ("Helvetica Neue", 10)
ROW_H     = 32

# ── file type → accent color ──────────────────────
EXT_COLORS = {
    ".py":    C["yellow"],  ".js":  C["yellow"],  ".ts":   C["yellow"],
    ".sh":    C["yellow"],  ".bash":C["yellow"],
    ".html":  C["peach"],   ".css": C["peach"],   ".jsx":  C["peach"],
    ".json":  C["green"],   ".yaml":C["green"],   ".yml":  C["green"],
    ".toml":  C["green"],
    ".png":   C["pink"],    ".jpg": C["pink"],    ".jpeg": C["pink"],
    ".gif":   C["pink"],    ".svg": C["pink"],    ".webp": C["pink"],
    ".mp4":   C["mauve"],   ".mov": C["mauve"],   ".avi":  C["mauve"],
    ".mkv":   C["mauve"],
    ".mp3":   C["sapphire"],".wav": C["sapphire"],".flac": C["sapphire"],
    ".aac":   C["sapphire"],
    ".pdf":   C["red"],
    ".zip":   C["peach"],   ".tar": C["peach"],   ".gz":   C["peach"],
    ".rar":   C["peach"],   ".7z":  C["peach"],
    ".md":    C["subtext"], ".txt": C["subtext"],
    ".app":   C["blue"],    ".dmg": C["blue"],    ".pkg":  C["blue"],
    ".doc":   C["lavender"],".docx":C["lavender"],
    ".xls":   C["lavender"],".xlsx":C["lavender"],
    ".ppt":   C["lavender"],".pptx":C["lavender"],
}

FILE_ICONS = {
    ".py":"🐍", ".js":"📜", ".ts":"📜", ".html":"🌐", ".css":"🎨",
    ".json":"📋", ".yaml":"📋", ".yml":"📋", ".toml":"📋",
    ".png":"🖼", ".jpg":"🖼", ".jpeg":"🖼", ".gif":"🖼",
    ".svg":"🖼", ".webp":"🖼",
    ".mp4":"🎬", ".mov":"🎬", ".avi":"🎬", ".mkv":"🎬",
    ".mp3":"🎵", ".wav":"🎵", ".flac":"🎵", ".aac":"🎵",
    ".pdf":"📕",
    ".zip":"🗜", ".tar":"🗜", ".gz":"🗜", ".rar":"🗜",
    ".md":"📝", ".txt":"📄",
    ".app":"📦", ".dmg":"💿", ".pkg":"💿",
    ".doc":"📝", ".docx":"📝", ".xls":"📊", ".xlsx":"📊",
    ".sh":"⚙️", ".bash":"⚙️",
}

def get_icon(name, is_dir):
    if is_dir:
        return "📁", C["blue"]
    ext = os.path.splitext(name)[1].lower()
    return FILE_ICONS.get(ext, "📄"), EXT_COLORS.get(ext, C["overlay1"])

def human_size(n):
    for u in ("B","KB","MB","GB","TB"):
        if n < 1024: return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"

def time_ago(ts):
    diff = time.time() - ts
    if diff < 60:     return "just now"
    if diff < 3600:   return f"{int(diff/60)}m ago"
    if diff < 86400:  return f"{int(diff/3600)}h ago"
    if diff < 604800: return f"{int(diff/86400)}d ago"
    return datetime.fromtimestamp(ts).strftime("%d %b %Y")


# ═══════════════════════════════════════════════════
#  TOOLTIP
# ═══════════════════════════════════════════════════
class Tooltip:
    def __init__(self, widget, text):
        self.w = widget; self.text = text; self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, e=None):
        x = self.w.winfo_rootx() + 20
        y = self.w.winfo_rooty() + self.w.winfo_height() + 4
        self.tip = tk.Toplevel(self.w)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text,
                 bg=C["surface1"], fg=C["text"],
                 font=FONT_XS, padx=8, pady=4).pack()

    def hide(self, e=None):
        if self.tip:
            self.tip.destroy(); self.tip = None


# ═══════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════
class Finder:

    PLACES = [
        ("🏠", "Home",       os.path.expanduser("~")),
        ("🖥", "Desktop",    os.path.expanduser("~/Desktop")),
        ("📂", "Documents",  os.path.expanduser("~/Documents")),
        ("⬇️", "Downloads",  os.path.expanduser("~/Downloads")),
        ("🎵", "Music",      os.path.expanduser("~/Music")),
        ("🖼", "Pictures",   os.path.expanduser("~/Pictures")),
        ("🎬", "Movies",     os.path.expanduser("~/Movies")),
        ("💾", "Root /",     "/"),
    ]

    def __init__(self, root):
        self.root        = root
        self.root.title("Finder")
        self.root.geometry("1200x740")
        self.root.configure(bg=C["crust"])
        self.root.minsize(900, 560)

        self.path        = os.path.expanduser("~")
        self.back_h      = []
        self.fwd_h       = []
        self._entries    = []
        self._sel        = -1
        self._hov        = -1
        self._clip       = None
        self.sort_col    = "name"
        self.sort_rev    = False
        self.show_hidden = False
        self._sb_btns    = []

        self._build()
        self._render()

    # ── BUILD ────────────────────────────────────────

    def _build(self):
        self._build_titlebar()
        self._build_body()
        self._build_statusbar()
        self._build_context_menu()

    def _build_titlebar(self):
        tb = tk.Frame(self.root, bg=C["mantle"], height=52)
        tb.pack(side=tk.TOP, fill=tk.X)
        tb.pack_propagate(False)

        # decorative traffic lights
        lights = tk.Frame(tb, bg=C["mantle"])
        lights.pack(side=tk.LEFT, padx=14, pady=16)
        for col in [C["red"], C["yellow"], C["green"]]:
            cv = tk.Canvas(lights, width=13, height=13,
                           bg=C["mantle"], highlightthickness=0)
            cv.pack(side=tk.LEFT, padx=3)
            cv.create_oval(1, 1, 12, 12, fill=col, outline="")

        # nav buttons
        nav = tk.Frame(tb, bg=C["mantle"])
        nav.pack(side=tk.LEFT, padx=4)
        self._tbtn(nav, "‹", self.go_back, "Back").pack(side=tk.LEFT, padx=2)
        self._tbtn(nav, "›", self.go_fwd,  "Forward").pack(side=tk.LEFT, padx=2)
        self._tbtn(nav, "↑", self.go_up,   "Parent folder").pack(side=tk.LEFT, padx=2)

        # path entry
        path_wrap = tk.Frame(tb, bg=C["surface0"],
                             highlightbackground=C["surface1"], highlightthickness=1)
        path_wrap.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=12, ipady=2)
        self.path_var = tk.StringVar(value=self.path)
        pe = tk.Entry(path_wrap, textvariable=self.path_var,
                      bg=C["surface0"], fg=C["text"],
                      insertbackground=C["blue"],
                      font=FONT_MONO, relief=tk.FLAT, bd=6,
                      selectbackground=C["blue"], selectforeground=C["crust"])
        pe.pack(fill=tk.X, expand=True)
        pe.bind("<Return>", lambda _: self.goto(self.path_var.get()))
        pe.bind("<FocusIn>",  lambda _: path_wrap.config(highlightbackground=C["blue"]))
        pe.bind("<FocusOut>", lambda _: path_wrap.config(highlightbackground=C["surface1"]))

        # search entry
        srch_wrap = tk.Frame(tb, bg=C["surface0"],
                             highlightbackground=C["surface1"], highlightthickness=1)
        srch_wrap.pack(side=tk.LEFT, padx=(0, 8), pady=12, ipady=2)
        tk.Label(srch_wrap, text="🔍", bg=C["surface0"],
                 font=("Helvetica", 13)).pack(side=tk.LEFT, padx=(6, 0))
        self.sv = tk.StringVar()
        self.sv.trace("w", lambda *_: self._render())
        se = tk.Entry(srch_wrap, textvariable=self.sv, width=18,
                      bg=C["surface0"], fg=C["text"],
                      insertbackground=C["blue"],
                      font=FONT_UI, relief=tk.FLAT, bd=4,
                      selectbackground=C["blue"])
        se.pack(side=tk.LEFT, padx=4)
        se.bind("<FocusIn>",  lambda _: srch_wrap.config(highlightbackground=C["blue"]))
        se.bind("<FocusOut>", lambda _: srch_wrap.config(highlightbackground=C["surface1"]))

        # hidden toggle
        self._tbtn(tb, "👁", self._toggle_hidden, "Toggle hidden files").pack(
            side=tk.LEFT, padx=(0, 10))

    def _build_body(self):
        body = tk.Frame(self.root, bg=C["base"])
        body.pack(fill=tk.BOTH, expand=True)

        # sidebar
        self._build_sidebar(body)
        tk.Frame(body, bg=C["surface0"], width=1).pack(side=tk.LEFT, fill=tk.Y)

        # center (header + list)
        center = tk.Frame(body, bg=C["base"])
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._build_col_header(center)
        self._build_filelist(center)

        # preview panel
        tk.Frame(body, bg=C["surface0"], width=1).pack(side=tk.LEFT, fill=tk.Y)
        self._build_preview(body)

    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=C["mantle"], width=190)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        sb.pack_propagate(False)

        tk.Label(sb, text="FAVOURITES", bg=C["mantle"], fg=C["overlay0"],
                 font=(FONT_XS[0], 10, "bold"), anchor="w", padx=18
                 ).pack(fill=tk.X, pady=(20, 6))

        for icon, label, path in self.PLACES:
            if not os.path.exists(path): continue
            btn = tk.Label(sb, text=f"  {icon}  {label}",
                           bg=C["mantle"], fg=C["subtext"],
                           font=FONT_UI, anchor="w", padx=10, pady=8,
                           cursor="hand2")
            btn.pack(fill=tk.X, padx=6, pady=1)
            btn.bind("<Button-1>", lambda e, p=path: self.goto(p))
            btn.bind("<Enter>",    lambda e, b=btn: b.config(
                bg=C["surface0"], fg=C["text"]) if self.path != path else None)
            btn.bind("<Leave>",    lambda e, b=btn, p=path: b.config(
                bg=C["blue"] if self.path == p else C["mantle"],
                fg=C["crust"] if self.path == p else C["subtext"]))
            self._sb_btns.append((btn, path))

        tk.Frame(sb, bg=C["surface0"], height=1).pack(fill=tk.X, padx=14, pady=12)
        tk.Label(sb, text="DEVICES", bg=C["mantle"], fg=C["overlay0"],
                 font=(FONT_XS[0], 10, "bold"), anchor="w", padx=18
                 ).pack(fill=tk.X, pady=(0, 6))

        hd = tk.Label(sb, text="  💽  Macintosh HD",
                      bg=C["mantle"], fg=C["subtext"],
                      font=FONT_UI, anchor="w", padx=10, pady=8, cursor="hand2")
        hd.pack(fill=tk.X, padx=6, pady=1)
        hd.bind("<Button-1>", lambda e: self.goto("/"))
        hd.bind("<Enter>",    lambda e: hd.config(bg=C["surface0"], fg=C["text"]))
        hd.bind("<Leave>",    lambda e: hd.config(bg=C["mantle"], fg=C["subtext"]))

    def _build_col_header(self, parent):
        hdr = tk.Frame(parent, bg=C["mantle"], height=30)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        for text, col in [("  Name","name"),("Size","size"),
                           ("Type","type"),("Modified","modified")]:
            lbl = tk.Label(hdr, text=text, bg=C["mantle"], fg=C["overlay0"],
                           font=(FONT_SM[0], 11, "bold"), anchor="w",
                           cursor="hand2", padx=6)
            lbl.pack(side=tk.LEFT, padx=2)
            lbl.bind("<Button-1>", lambda e, c=col: self._sort(c))
            lbl.bind("<Enter>",    lambda e, l=lbl: l.config(fg=C["text"]))
            lbl.bind("<Leave>",    lambda e, l=lbl: l.config(fg=C["overlay0"]))

    def _build_filelist(self, parent):
        cf = tk.Frame(parent, bg=C["base"])
        cf.pack(fill=tk.BOTH, expand=True)
        cf.rowconfigure(0, weight=1)
        cf.columnconfigure(0, weight=1)

        self.cv = tk.Canvas(cf, bg=C["base"], highlightthickness=0, bd=0)
        ys = tk.Scrollbar(cf, orient=tk.VERTICAL, command=self.cv.yview,
                          bg=C["mantle"], troughcolor=C["base"])
        self.cv.config(yscrollcommand=ys.set)
        self.cv.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")

        self.cv.bind("<Configure>",        self._on_resize)
        self.cv.bind("<Button-1>",         self._on_click)
        self.cv.bind("<Double-Button-1>",  self._on_double)
        self.cv.bind("<Button-2>",         self._on_rclick)
        self.cv.bind("<Control-Button-1>", self._on_rclick)
        self.cv.bind("<Motion>",           self._on_motion)
        self.cv.bind("<Leave>",            self._on_leave)
        self.cv.bind("<MouseWheel>",       self._on_scroll)
        self.cv.bind("<Key>",              self._on_key)
        self.cv.bind("<ButtonPress-1>",    lambda e: self.cv.focus_set())

    def _build_preview(self, parent):
        pf = tk.Frame(parent, bg=C["mantle"], width=240)
        pf.pack(side=tk.LEFT, fill=tk.Y)
        pf.pack_propagate(False)

        tk.Label(pf, text="PREVIEW", bg=C["mantle"], fg=C["overlay0"],
                 font=(FONT_XS[0], 10, "bold"), anchor="w", padx=16
                 ).pack(fill=tk.X, pady=(18, 6))
        tk.Frame(pf, bg=C["surface0"], height=1).pack(fill=tk.X, padx=14, pady=(0, 16))

        self.prev_icon = tk.Label(pf, text="", bg=C["mantle"],
                                  font=("Helvetica", 52))
        self.prev_icon.pack(pady=(16, 8))

        self.prev_name = tk.Label(pf, text="Select a file",
                                  bg=C["mantle"], fg=C["text"],
                                  font=(FONT_UI[0], 13, "bold"),
                                  wraplength=210, justify=tk.CENTER)
        self.prev_name.pack(padx=12)

        self.prev_kind = tk.Label(pf, text="",
                                  bg=C["mantle"], fg=C["overlay1"],
                                  font=FONT_SM)
        self.prev_kind.pack(pady=(4, 0))

        tk.Frame(pf, bg=C["surface0"], height=1).pack(fill=tk.X, padx=14, pady=14)

        self._meta_vals = {}
        for label in ("Size", "Modified", "Created", "Permissions"):
            row = tk.Frame(pf, bg=C["mantle"])
            row.pack(fill=tk.X, padx=16, pady=3)
            tk.Label(row, text=label + ":", bg=C["mantle"],
                     fg=C["overlay0"], font=FONT_XS, width=12, anchor="w"
                     ).pack(side=tk.LEFT)
            v = tk.Label(row, text="", bg=C["mantle"],
                         fg=C["subtext"], font=FONT_XS, anchor="w")
            v.pack(side=tk.LEFT)
            self._meta_vals[label] = v

        tk.Frame(pf, bg=C["surface0"], height=1).pack(fill=tk.X, padx=14, pady=14)

        for text, cmd in [("  Open  ", self.m_open),
                           ("  Open in Terminal  ", self.m_terminal),
                           ("  Get Info  ", self.m_info)]:
            b = tk.Label(pf, text=text, bg=C["surface0"],
                         fg=C["text"], font=FONT_SM, pady=7,
                         cursor="hand2")
            b.pack(fill=tk.X, padx=14, pady=3)
            b.bind("<Button-1>", lambda e, c=cmd: c())
            b.bind("<Enter>",    lambda e, w=b: w.config(bg=C["surface1"]))
            b.bind("<Leave>",    lambda e, w=b: w.config(bg=C["surface0"]))

    def _build_statusbar(self):
        sb = tk.Frame(self.root, bg=C["mantle"], height=36)
        sb.pack(side=tk.BOTTOM, fill=tk.X)
        sb.pack_propagate(False)

        act = tk.Frame(sb, bg=C["mantle"])
        act.pack(side=tk.LEFT, padx=10, pady=6)

        for text, cmd, tip in [("+ Folder", self.new_folder, "New folder"),
                                ("+ File",   self.new_file,   "New file")]:
            b = tk.Label(act, text=text, bg=C["surface0"], fg=C["text"],
                         font=FONT_SM, padx=12, pady=4, cursor="hand2")
            b.pack(side=tk.LEFT, padx=3)
            b.bind("<Button-1>", lambda e, c=cmd: c())
            b.bind("<Enter>",    lambda e, w=b: w.config(bg=C["surface1"]))
            b.bind("<Leave>",    lambda e, w=b: w.config(bg=C["surface0"]))
            Tooltip(b, tip)

        self.status_var = tk.StringVar()
        tk.Label(sb, textvariable=self.status_var,
                 bg=C["mantle"], fg=C["overlay0"], font=FONT_SM
                 ).pack(side=tk.RIGHT, padx=16)

    def _build_context_menu(self):
        self.menu = tk.Menu(self.root, tearoff=0,
                            bg=C["surface0"], fg=C["text"],
                            activebackground=C["blue"],
                            activeforeground=C["crust"],
                            font=FONT_UI, relief=tk.FLAT, bd=0)
        self.menu.add_command(label="  Open",               command=self.m_open)
        self.menu.add_command(label="  Open in Terminal",   command=self.m_terminal)
        self.menu.add_command(label="  Reveal in Finder",   command=self.m_reveal)
        self.menu.add_separator()
        self.menu.add_command(label="  Rename",             command=self.m_rename)
        self.menu.add_command(label="  Duplicate",          command=self.m_duplicate)
        self.menu.add_separator()
        self.menu.add_command(label="  Copy",               command=self.m_copy)
        self.menu.add_command(label="  Cut",                command=self.m_cut)
        self.menu.add_command(label="  Paste",              command=self.m_paste)
        self.menu.add_separator()
        self.menu.add_command(label="  Get Info",           command=self.m_info)
        self.menu.add_separator()
        self.menu.add_command(label="  Move to Trash",      command=self.m_trash)

    # ── WIDGET HELPER ────────────────────────────────

    def _tbtn(self, parent, text, cmd, tip=None):
        b = tk.Label(parent, text=text, bg=C["surface0"], fg=C["text"],
                     font=("Helvetica", 15), padx=10, pady=4, cursor="hand2")
        b.bind("<Button-1>", lambda e: cmd())
        b.bind("<Enter>",    lambda e: b.config(bg=C["surface1"]))
        b.bind("<Leave>",    lambda e: b.config(bg=C["surface0"]))
        if tip: Tooltip(b, tip)
        return b

    def _update_sidebar(self):
        for btn, path in self._sb_btns:
            if self.path == path:
                btn.config(bg=C["blue"], fg=C["crust"])
            else:
                btn.config(bg=C["mantle"], fg=C["subtext"])

    # ── NAVIGATION ───────────────────────────────────

    def goto(self, path, push=True):
        path = os.path.expanduser(str(path).strip())
        if not os.path.isdir(path):
            messagebox.showerror("Not found", f"Not a directory:\n{path}"); return
        if push and path != self.path:
            self.back_h.append(self.path); self.fwd_h.clear()
        self.path = path
        self.path_var.set(path)
        self.sv.set("")
        self._sel = -1
        self._update_sidebar()
        self._render()

    def go_back(self):
        if self.back_h:
            self.fwd_h.append(self.path)
            self.goto(self.back_h.pop(), push=False)

    def go_fwd(self):
        if self.fwd_h:
            self.back_h.append(self.path)
            self.goto(self.fwd_h.pop(), push=False)

    def go_up(self):
        p = os.path.dirname(self.path)
        if p != self.path: self.goto(p)

    def _toggle_hidden(self):
        self.show_hidden = not self.show_hidden
        self._render()

    # ── RENDER ───────────────────────────────────────

    def _render(self):
        self._hov = -1
        kw = self.sv.get().lower()
        try:
            names = os.listdir(self.path)
        except PermissionError:
            messagebox.showerror("Permission Denied",
                "System Settings → Privacy & Security → Full Disk Access → enable Terminal")
            return
        except Exception as ex:
            messagebox.showerror("Error", str(ex)); return

        entries = []
        for name in names:
            if not self.show_hidden and name.startswith("."): continue
            if kw and kw not in name.lower(): continue
            full   = os.path.join(self.path, name)
            is_dir = os.path.isdir(full)
            try:
                st = os.stat(full)
                entries.append({
                    "name":     name,
                    "full":     full,
                    "is_dir":   is_dir,
                    "size":     st.st_size,
                    "modified": st.st_mtime,
                    "created":  getattr(st, "st_birthtime", st.st_mtime),
                    "perms":    oct(st.st_mode)[-3:],
                    "type":     "Folder" if is_dir else
                                (os.path.splitext(name)[1].lstrip(".").upper() or "File"),
                })
            except: pass

        entries.sort(key=lambda e: (
            not e["is_dir"],
            e[self.sort_col].lower() if isinstance(e[self.sort_col], str)
            else e[self.sort_col]
        ), reverse=self.sort_rev)

        self._entries = entries
        self._sel = min(self._sel, len(entries) - 1)
        self._draw()
        self._update_preview()

        try:
            _, _, free = shutil.disk_usage(self.path)
            disk = f"   ·   {human_size(free)} available"
        except: disk = ""
        n = len(entries)
        self.status_var.set(f"{n} item{'s' if n != 1 else ''}{disk}")

    def _draw(self):
        cv = self.cv
        cv.delete("all")
        W = max(cv.winfo_width(), 700)

        for i, e in enumerate(self._entries):
            y = i * ROW_H

            if i == self._sel:
                bg = C["blue"]
            elif i == self._hov:
                bg = C["surface0"]
            else:
                bg = C["base"] if i % 2 == 0 else C["mantle"]

            cv.create_rectangle(0, y, W, y + ROW_H, fill=bg, outline="")

            fg     = C["crust"]   if i == self._sel else C["text"]
            fg_dim = C["surface1"] if i == self._sel else C["overlay0"]

            icon, icolor = get_icon(e["name"], e["is_dir"])
            ic = C["crust"] if i == self._sel else icolor

            # icon
            cv.create_text(22, y + ROW_H // 2, text=icon,
                           font=("Helvetica", 17), fill=ic, anchor="center")

            # colored dot for file type (only for files, not selected)
            if not e["is_dir"] and i != self._sel:
                cv.create_oval(34, y + ROW_H // 2 - 3,
                               39, y + ROW_H // 2 + 3,
                               fill=EXT_COLORS.get(
                                   os.path.splitext(e["name"])[1].lower(),
                                   C["overlay1"]),
                               outline="")

            # name
            cv.create_text(48, y + ROW_H // 2, text=e["name"],
                           anchor="w", font=FONT_UI, fill=fg)

            # size
            size_t = "—" if e["is_dir"] else human_size(e["size"])
            cv.create_text(490, y + ROW_H // 2, text=size_t,
                           anchor="w", font=FONT_SM, fill=fg_dim)

            # type badge
            pill_x = 590
            pill_w = max(len(e["type"]) * 7 + 14, 44)
            pill_bg = C["surface1"] if i != self._sel else C["sapphire"]
            cv.create_rectangle(pill_x, y + ROW_H // 2 - 10,
                                pill_x + pill_w, y + ROW_H // 2 + 10,
                                fill=pill_bg, outline="")
            cv.create_text(pill_x + pill_w // 2, y + ROW_H // 2,
                           text=e["type"], font=FONT_XS,
                           fill=C["text"] if i != self._sel else C["crust"])

            # modified
            cv.create_text(720, y + ROW_H // 2, text=time_ago(e["modified"]),
                           anchor="w", font=FONT_SM, fill=fg_dim)

            # row separator
            if i != self._sel and i != self._hov:
                cv.create_line(48, y + ROW_H - 1, W, y + ROW_H - 1,
                               fill=C["surface0"])

        if not self._entries:
            cv.create_text(W // 2, 120, text="This folder is empty",
                           font=(FONT_UI[0], 16), fill=C["overlay0"])

        H = max(len(self._entries) * ROW_H + 40, cv.winfo_height())
        cv.config(scrollregion=(0, 0, W, H))

    def _update_preview(self):
        if self._sel < 0 or self._sel >= len(self._entries):
            self.prev_icon.config(text="")
            self.prev_name.config(text="Select a file")
            self.prev_kind.config(text="")
            for v in self._meta_vals.values(): v.config(text="")
            return

        e = self._entries[self._sel]
        icon, _ = get_icon(e["name"], e["is_dir"])
        self.prev_icon.config(text=icon)
        self.prev_name.config(text=e["name"])
        self.prev_kind.config(text=e["type"])
        self._meta_vals["Size"].config(
            text="—" if e["is_dir"] else human_size(e["size"]))
        self._meta_vals["Modified"].config(
            text=datetime.fromtimestamp(e["modified"]).strftime("%d %b %Y %H:%M"))
        self._meta_vals["Created"].config(
            text=datetime.fromtimestamp(e["created"]).strftime("%d %b %Y"))
        self._meta_vals["Permissions"].config(text=e["perms"])

    def _sort(self, col):
        self.sort_rev = (not self.sort_rev) if self.sort_col == col else False
        self.sort_col = col
        self._render()

    # ── EVENTS ───────────────────────────────────────

    def _row_at(self, y):
        i = int(self.cv.canvasy(y) // ROW_H)
        return i if 0 <= i < len(self._entries) else -1

    def _on_resize(self, _): self._draw()

    def _on_motion(self, e):
        i = self._row_at(e.y)
        if i != self._hov: self._hov = i; self._draw()

    def _on_leave(self, _):
        self._hov = -1; self._draw()

    def _on_scroll(self, e):
        self.cv.yview_scroll(int(-1 * (e.delta / 120)), "units")

    def _on_click(self, e):
        self._sel = self._row_at(e.y)
        self._draw(); self._update_preview()

    def _on_double(self, e):
        i = self._row_at(e.y)
        if i < 0: return
        ent = self._entries[i]
        self.goto(ent["full"]) if ent["is_dir"] else subprocess.Popen(["open", ent["full"]])

    def _on_rclick(self, e):
        i = self._row_at(e.y)
        if i >= 0:
            self._sel = i; self._draw(); self._update_preview()
            self.menu.tk_popup(e.x_root, e.y_root)

    def _on_key(self, e):
        if e.keysym == "Up":
            self._sel = max(0, self._sel - 1)
        elif e.keysym == "Down":
            self._sel = min(len(self._entries) - 1, self._sel + 1)
        elif e.keysym == "Return" and self._sel >= 0:
            ent = self._entries[self._sel]
            self.goto(ent["full"]) if ent["is_dir"] else subprocess.Popen(["open", ent["full"]])
        elif e.keysym == "BackSpace":
            self.go_up()
        self._draw(); self._update_preview()

    def _sel_path(self):
        if 0 <= self._sel < len(self._entries):
            return self._entries[self._sel]["full"]
        return None

    def _sel_entry(self):
        if 0 <= self._sel < len(self._entries):
            return self._entries[self._sel]
        return None

    # ── MENU ACTIONS ─────────────────────────────────

    def m_open(self):
        p = self._sel_path()
        if p: self.goto(p) if os.path.isdir(p) else subprocess.Popen(["open", p])

    def m_terminal(self):
        p = self._sel_path() or self.path
        subprocess.Popen(["open", "-a", "Terminal",
                          p if os.path.isdir(p) else os.path.dirname(p)])

    def m_reveal(self):
        p = self._sel_path() or self.path
        subprocess.Popen(["open", "-R", p])

    def m_rename(self):
        p = self._sel_path()
        if not p: return
        new = simpledialog.askstring("Rename", "New name:",
                                     initialvalue=os.path.basename(p), parent=self.root)
        if new:
            try: os.rename(p, os.path.join(os.path.dirname(p), new)); self._render()
            except Exception as ex: messagebox.showerror("Error", str(ex))

    def m_duplicate(self):
        p = self._sel_path()
        if not p: return
        name, ext = os.path.splitext(os.path.basename(p))
        dst = os.path.join(os.path.dirname(p), f"{name} copy{ext}")
        try:
            shutil.copytree(p, dst) if os.path.isdir(p) else shutil.copy2(p, dst)
            self._render()
        except Exception as ex: messagebox.showerror("Error", str(ex))

    def m_copy(self):
        p = self._sel_path()
        if p: self._clip = (p, "copy"); self.status_var.set(f"Copied: {os.path.basename(p)}")

    def m_cut(self):
        p = self._sel_path()
        if p: self._clip = (p, "cut"); self.status_var.set(f"Cut: {os.path.basename(p)}")

    def m_paste(self):
        if not self._clip: return
        src, op = self._clip
        dst = os.path.join(self.path, os.path.basename(src))
        try:
            if op == "copy":
                shutil.copytree(src, dst) if os.path.isdir(src) else shutil.copy2(src, dst)
            else:
                shutil.move(src, dst); self._clip = None
            self._render()
        except Exception as ex: messagebox.showerror("Error", str(ex))

    def m_info(self):
        e = self._sel_entry()
        if not e: return
        info = (f"Name:         {e['name']}\n"
                f"Path:         {e['full']}\n"
                f"Type:         {e['type']}\n"
                f"Size:         {'—' if e['is_dir'] else human_size(e['size'])}\n"
                f"Modified:     {datetime.fromtimestamp(e['modified']).strftime('%d %b %Y  %H:%M')}\n"
                f"Created:      {datetime.fromtimestamp(e['created']).strftime('%d %b %Y  %H:%M')}\n"
                f"Permissions:  {e['perms']}")
        messagebox.showinfo(f"Info — {e['name']}", info, parent=self.root)

    def m_trash(self):
        p = self._sel_path()
        if not p: return
        if messagebox.askyesno("Move to Trash",
                               f'Move "{os.path.basename(p)}" to Trash?',
                               parent=self.root):
            try:
                subprocess.run(["osascript", "-e",
                    f'tell application "Finder" to delete POSIX file "{p}"'],
                    check=True)
                self._sel = -1; self._render()
            except Exception as ex: messagebox.showerror("Error", str(ex))

    def new_folder(self):
        n = simpledialog.askstring("New Folder", "Folder name:", parent=self.root)
        if n:
            try: os.makedirs(os.path.join(self.path, n), exist_ok=True); self._render()
            except Exception as ex: messagebox.showerror("Error", str(ex))

    def new_file(self):
        n = simpledialog.askstring("New File", "File name:", parent=self.root)
        if n:
            try: open(os.path.join(self.path, n), "w").close(); self._render()
            except Exception as ex: messagebox.showerror("Error", str(ex))


if __name__ == "__main__":
    root = tk.Tk()
    Finder(root)
    root.mainloop()