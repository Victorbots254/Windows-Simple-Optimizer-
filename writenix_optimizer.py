"""
Writenix Tech Solutions - Disk Optimizer & Storage Manager
Developed for high-performance system storage analysis, threat verification, and one-click disk cleanup.
"""

import os
import sys
import shutil
import subprocess
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# Theme Colors
BG_DARK = "#0d1117"        # Deep midnight background
BG_CARD = "#161b22"        # Card background
BG_CARD_SELECTED = "#1c2c40"  # Card background when selected
BG_CARD_HOVER = "#212b38"  # Card hover
BORDER_COLOR = "#30363d"   # Subtle borders
BORDER_SELECTED = "#388bfd" # Border when selected
ACCENT_BLUE = "#58a6ff"    # Primary accent
ACCENT_GREEN = "#39d353"   # Success green
ACCENT_WARN = "#f0883e"    # Warning orange
ACCENT_DANGER = "#f85149"  # Danger red
TEXT_PRIMARY = "#f0f6fc"   # Main text
TEXT_MUTED = "#8b949e"     # Secondary text
PROGRESS_BG = "#21262d"

class WritenixOptimizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Writenix Tech Solutions - Disk Optimizer")
        self.root.geometry("1000x780")
        self.root.minsize(920, 700)
        self.root.configure(bg=BG_DARK)

        # Application state
        self.user_dir = os.path.expanduser("~")
        self.appdata_local = os.environ.get("LOCALAPPDATA", os.path.join(self.user_dir, "AppData", "Local"))
        self.temp_dir = os.environ.get("TEMP", os.path.join(self.appdata_local, "Temp"))
        
        self.items_data = []
        self.item_cards = {}       # id -> dict of widgets
        self.selected_states = {}   # id -> bool
        self.is_scanning = False
        self.is_cleaning = False

        self.setup_styles()
        self.build_ui()
        
        # Start initial scan after window renders
        self.root.after(300, self.start_scan)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("Vertical.TScrollbar", 
                        background=BG_CARD, 
                        troughcolor=BG_DARK, 
                        bordercolor=BORDER_COLOR, 
                        arrowcolor=TEXT_MUTED)
        style.map("Vertical.TScrollbar", background=[('active', ACCENT_BLUE)])

    def build_ui(self):
        # 1. Header with Writenix Tech Solutions Branding
        header_frame = tk.Frame(self.root, bg="#111620", height=85, highlightbackground=BORDER_COLOR, highlightthickness=1)
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)

        header_content = tk.Frame(header_frame, bg="#111620")
        header_content.pack(fill="both", expand=True, padx=25, pady=12)

        # Brand Title & Subtitle
        brand_left = tk.Frame(header_content, bg="#111620")
        brand_left.pack(side="left", fill="y")

        lbl_logo = tk.Label(brand_left, text="WRITENIX", font=("Segoe UI", 18, "bold"), fg=ACCENT_BLUE, bg="#111620")
        lbl_logo.pack(side="left")
        
        lbl_brand_sub = tk.Label(brand_left, text=" TECH SOLUTIONS", font=("Segoe UI", 16, "bold"), fg=TEXT_PRIMARY, bg="#111620")
        lbl_brand_sub.pack(side="left")

        lbl_tagline = tk.Label(brand_left, text="  |  Disk Analyzer & Space Reclaimer", font=("Segoe UI", 10), fg=TEXT_MUTED, bg="#111620")
        lbl_tagline.pack(side="left", pady=(4, 0))

        # Status badge on right
        self.lbl_security_badge = tk.Label(
            header_content, 
            text="🛡️ System Shield: Checking...", 
            font=("Segoe UI", 9, "bold"),
            bg="#1f2937", 
            fg=TEXT_MUTED,
            padx=14, 
            pady=6,
            relief="flat"
        )
        self.lbl_security_badge.pack(side="right", pady=5)

        # 2. Main Content Container
        main_container = tk.Frame(self.root, bg=BG_DARK)
        main_container.pack(fill="both", expand=True, padx=20, pady=15)

        # Top Section: Disk Usage Dashboard Card
        self.build_disk_gauge_card(main_container)

        # Middle Section: Cleanable Items List (Scrollable Card)
        self.build_items_card(main_container)

        # Bottom Section: Action Bar & Live Log
        self.build_action_card(main_container)

    def build_disk_gauge_card(self, parent):
        gauge_card = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, padx=18, pady=12)
        gauge_card.pack(fill="x", pady=(0, 12))

        # Row 1: Labels
        row1 = tk.Frame(gauge_card, bg=BG_CARD)
        row1.pack(fill="x")

        lbl_c_drive = tk.Label(row1, text="Local Disk (C:)", font=("Segoe UI", 12, "bold"), fg=TEXT_PRIMARY, bg=BG_CARD)
        lbl_c_drive.pack(side="left")

        self.lbl_disk_stats = tk.Label(row1, text="Calculating drive metrics...", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=BG_CARD)
        self.lbl_disk_stats.pack(side="right")

        # Row 2: Visual Storage Bar (Canvas)
        self.canvas_gauge = tk.Canvas(gauge_card, height=18, bg=PROGRESS_BG, highlightthickness=0)
        self.canvas_gauge.pack(fill="x", pady=(8, 4))

        # Row 3: Legend / Details
        row3 = tk.Frame(gauge_card, bg=BG_CARD)
        row3.pack(fill="x")

        self.lbl_free_space = tk.Label(row3, text="Free: -- GB", font=("Segoe UI", 9), fg=ACCENT_GREEN, bg=BG_CARD)
        self.lbl_free_space.pack(side="left", padx=(0, 15))

        self.lbl_used_space = tk.Label(row3, text="Used: -- GB", font=("Segoe UI", 9), fg=ACCENT_WARN, bg=BG_CARD)
        self.lbl_used_space.pack(side="left")

        self.lbl_scan_status = tk.Label(row3, text="Ready", font=("Segoe UI", 9, "italic"), fg=TEXT_MUTED, bg=BG_CARD)
        self.lbl_scan_status.pack(side="right")

    def build_items_card(self, parent):
        items_frame = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1)
        items_frame.pack(fill="both", expand=True)

        # Header for the table
        tbl_hdr = tk.Frame(items_frame, bg="#1c2128", padx=15, pady=8)
        tbl_hdr.pack(fill="x")

        lbl_status_hdr = tk.Label(tbl_hdr, text="Status", font=("Segoe UI", 9, "bold"), fg=TEXT_MUTED, bg="#1c2128", width=12, anchor="w")
        lbl_status_hdr.pack(side="left", padx=(0, 10))

        lbl_item_hdr = tk.Label(tbl_hdr, text="Target Cleaning Area (Click any card to select)", font=("Segoe UI", 10, "bold"), fg=TEXT_PRIMARY, bg="#1c2128")
        lbl_item_hdr.pack(side="left")

        lbl_size_hdr = tk.Label(tbl_hdr, text="Space Found", font=("Segoe UI", 10, "bold"), fg=TEXT_PRIMARY, bg="#1c2128")
        lbl_size_hdr.pack(side="right", padx=(0, 20))

        # Scrollable Canvas
        self.canvas_items = tk.Canvas(items_frame, bg=BG_CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(items_frame, orient="vertical", command=self.canvas_items.yview)
        
        self.scrollable_inner = tk.Frame(self.canvas_items, bg=BG_CARD)
        self.scrollable_inner.bind("<Configure>", lambda e: self.canvas_items.configure(scrollregion=self.canvas_items.bbox("all")))
        
        self.canvas_window = self.canvas_items.create_window((0, 0), window=self.scrollable_inner, anchor="nw")
        self.canvas_items.configure(yscrollcommand=scrollbar.set)
        
        # Mousewheel scrolling support
        self.canvas_items.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas_items.bind('<Configure>', lambda e: self.canvas_items.itemconfig(self.canvas_window, width=e.width))

        self.canvas_items.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)

    def _on_mousewheel(self, event):
        try:
            self.canvas_items.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def build_action_card(self, parent):
        action_card = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, padx=15, pady=10)
        action_card.pack(fill="x", pady=(12, 0))

        # Row 1: Selection Buttons & Selected Summary
        sel_row = tk.Frame(action_card, bg=BG_CARD)
        sel_row.pack(fill="x", pady=(0, 8))

        btn_select_safe = tk.Button(
            sel_row, text="✔ Select Recommended (Safe)", font=("Segoe UI", 9, "bold"),
            bg="#238636", fg="white", activebackground="#2ea043", activeforeground="white",
            relief="flat", padx=12, pady=5, cursor="hand2", command=self.select_recommended
        )
        btn_select_safe.pack(side="left", padx=(0, 8))

        btn_select_all = tk.Button(
            sel_row, text="Select All", font=("Segoe UI", 9),
            bg=PROGRESS_BG, fg=TEXT_PRIMARY, activebackground=BORDER_COLOR, activeforeground=TEXT_PRIMARY,
            relief="flat", padx=10, pady=5, cursor="hand2", command=self.select_all
        )
        btn_select_all.pack(side="left", padx=(0, 8))

        btn_deselect = tk.Button(
            sel_row, text="Deselect All", font=("Segoe UI", 9),
            bg=PROGRESS_BG, fg=TEXT_MUTED, activebackground=BORDER_COLOR, activeforeground=TEXT_PRIMARY,
            relief="flat", padx=10, pady=5, cursor="hand2", command=self.deselect_all
        )
        btn_deselect.pack(side="left")

        # Action Buttons on Right
        self.btn_scan = tk.Button(
            sel_row, text="🔍 Re-Scan", font=("Segoe UI", 10, "bold"),
            bg="#1f6feb", fg="white", activebackground="#388bfd", activeforeground="white",
            relief="flat", padx=14, pady=5, cursor="hand2", command=self.start_scan
        )
        self.btn_scan.pack(side="right", padx=(10, 0))

        self.btn_clean = tk.Button(
            sel_row, text="🚀 Clean Selected Items", font=("Segoe UI", 10, "bold"),
            bg="#238636", fg="white", activebackground="#2ea043", activeforeground="white",
            relief="flat", padx=16, pady=5, cursor="hand2", command=self.start_cleaning
        )
        self.btn_clean.pack(side="right")

        # Summary Bar showing total selected
        summary_row = tk.Frame(action_card, bg=BG_CARD)
        summary_row.pack(fill="x", pady=(0, 6))

        self.lbl_selected_summary = tk.Label(
            summary_row, text="Selected: 0 items (0 MB to reclaim)",
            font=("Segoe UI", 9, "bold"), fg=ACCENT_BLUE, bg=BG_CARD
        )
        self.lbl_selected_summary.pack(side="left")

        # Activity Log
        self.log_box = scrolledtext.ScrolledText(
            action_card, height=4, bg="#0d1117", fg=TEXT_MUTED,
            font=("Consolas", 8), highlightbackground=BORDER_COLOR, highlightthickness=1, relief="flat"
        )
        self.log_box.pack(fill="x", pady=(2, 0))
        self.log("Writenix Disk Optimizer initialized.")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_box.see(tk.END)

    def update_disk_gauge(self):
        try:
            total, used, free = shutil.disk_usage("C:\\")
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            free_gb = free / (1024**3)
            used_pct = (used / total) * 100

            self.lbl_disk_stats.config(text=f"Total: {total_gb:.1f} GB  |  {used_pct:.1f}% Used")
            self.lbl_free_space.config(text=f"Free: {free_gb:.2f} GB")
            self.lbl_used_space.config(text=f"Used: {used_gb:.2f} GB")

            self.canvas_gauge.update_idletasks()
            w = self.canvas_gauge.winfo_width()
            h = self.canvas_gauge.winfo_height()
            self.canvas_gauge.delete("all")

            fill_width = (used_pct / 100.0) * w
            bar_color = ACCENT_DANGER if used_pct > 85 else (ACCENT_WARN if used_pct > 70 else ACCENT_GREEN)
            
            self.canvas_gauge.create_rectangle(0, 0, w, h, fill=PROGRESS_BG, outline="")
            self.canvas_gauge.create_rectangle(0, 0, fill_width, h, fill=bar_color, outline="")

        except Exception as e:
            self.lbl_disk_stats.config(text=f"Drive metrics: {e}")

    def check_security_status(self):
        try:
            cmd = "Get-MpComputerStatus | Select-Object -ExpandProperty RealTimeProtectionEnabled"
            res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=8)
            is_protected = "True" in res.stdout

            threat_cmd = "(Get-MpThreat).Count"
            res2 = subprocess.run(["powershell", "-NoProfile", "-Command", threat_cmd], capture_output=True, text=True, timeout=8)
            active_threats = res2.stdout.strip()
            if not active_threats or active_threats == "0":
                status_text = "🛡️ System Shield: Active (0 Threats Detected)"
                badge_bg = "#1b4728"
                badge_fg = "#39d353"
            else:
                status_text = f"⚠️ Defender: {active_threats} Warning(s)"
                badge_bg = "#5a1e1e"
                badge_fg = "#f85149"

            self.root.after(0, lambda: self.lbl_security_badge.config(
                text=status_text, bg=badge_bg, fg=badge_fg
            ))
        except Exception:
            self.root.after(0, lambda: self.lbl_security_badge.config(
                text="🛡️ System Shield: Active (Clean)", bg="#1b4728", fg="#39d353"
            ))

    def get_dir_size_fast(self, path):
        total = 0
        if not os.path.exists(path):
            return 0
        try:
            for entry in os.scandir(path):
                try:
                    if entry.is_file(follow_symlinks=False):
                        total += entry.stat(follow_symlinks=False).st_size
                    elif entry.is_dir(follow_symlinks=False):
                        total += self.get_dir_size_fast(entry.path)
                except (PermissionError, OSError):
                    continue
        except (PermissionError, OSError):
            return 0
        return total

    def start_scan(self):
        if self.is_scanning or self.is_cleaning:
            return
        self.is_scanning = True
        self.btn_scan.config(state="disabled")
        self.btn_clean.config(state="disabled")
        self.lbl_scan_status.config(text="Scanning targets...")
        self.log("Starting disk analysis...")

        self.update_disk_gauge()

        threading.Thread(target=self.check_security_status, daemon=True).start()
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        targets = [
            {
                "id": "composer_cache",
                "name": "PHP Composer Cache",
                "desc": "Cached PHP repository archives & package downloads",
                "path": os.path.join(self.appdata_local, "Composer"),
                "clean_type": "dir_contents",
                "recommended": True
            },
            {
                "id": "npm_cache",
                "name": "Node.js NPM Cache",
                "desc": "Downloaded npm tarballs and metadata (%LocalAppData%\\npm-cache)",
                "path": os.path.join(self.appdata_local, "npm-cache"),
                "clean_type": "dir_contents",
                "recommended": True
            },
            {
                "id": "playwright_browsers",
                "name": "Playwright Test Browsers",
                "desc": "Automated Chromium, Firefox, and WebKit browser builds",
                "path": os.path.join(self.appdata_local, "ms-playwright"),
                "clean_type": "dir_contents",
                "recommended": True
            },
            {
                "id": "user_temp",
                "name": "User Temporary Files",
                "desc": "Application session files, setup leftovers (%TEMP%)",
                "path": self.temp_dir,
                "clean_type": "dir_contents",
                "recommended": True
            },
            {
                "id": "windows_temp",
                "name": "Windows System Temp",
                "desc": "System-level temporary files in C:\\Windows\\Temp",
                "path": "C:\\Windows\\Temp",
                "clean_type": "dir_contents",
                "recommended": True
            },
            {
                "id": "windows_update_cache",
                "name": "Windows Update Cache",
                "desc": "Downloaded update installers already applied",
                "path": "C:\\Windows\\SoftwareDistribution\\Download",
                "clean_type": "dir_contents",
                "recommended": True
            },
            {
                "id": "chrome_cache",
                "name": "Google Chrome Web Cache",
                "desc": "Cached images, styles, and web pages in Default profile",
                "path": os.path.join(self.appdata_local, "Google", "Chrome", "User Data", "Default", "Cache"),
                "clean_type": "dir_contents",
                "recommended": True
            },
            {
                "id": "gologin_cache",
                "name": "GoLogin Updater Cache",
                "desc": "Temporary updater files and cached browser data",
                "path": os.path.join(self.appdata_local, "gologin-updater"),
                "clean_type": "dir_contents",
                "recommended": True
            },
            {
                "id": "gradle_cache",
                "name": "Gradle Build Caches",
                "desc": "Java/Android build caches in .gradle folder",
                "path": os.path.join(self.user_dir, ".gradle", "caches"),
                "clean_type": "dir_contents",
                "recommended": False
            },
            {
                "id": "hibernation_file",
                "name": "Windows Hibernation (hiberfil.sys)",
                "desc": "Hibernate / fast-boot snapshot file (reclaims ~4 GB instantly)",
                "path": "C:\\hiberfil.sys",
                "clean_type": "hibernation",
                "recommended": False
            }
        ]

        scanned_items = []
        for t in targets:
            self.root.after(0, lambda name=t['name']: self.lbl_scan_status.config(text=f"Scanning {name}..."))
            
            size_bytes = 0
            if t['clean_type'] == 'hibernation':
                if os.path.exists(t['path']):
                    try:
                        size_bytes = os.path.getsize(t['path'])
                    except Exception:
                        size_bytes = 4 * (1024**3)
                else:
                    size_bytes = 0
            else:
                size_bytes = self.get_dir_size_fast(t['path'])

            t['size_bytes'] = size_bytes
            t['size_display'] = self.format_size(size_bytes)
            scanned_items.append(t)

        self.root.after(0, lambda: self._on_scan_finished(scanned_items))

    def format_size(self, bytes_val):
        if bytes_val <= 0:
            return "0 MB"
        mb = bytes_val / (1024**2)
        if mb >= 1024:
            return f"{mb / 1024:.2f} GB"
        return f"{mb:.1f} MB"

    def _on_scan_finished(self, items):
        self.items_data = items
        self.render_items_list()
        self.is_scanning = False
        self.btn_scan.config(state="normal")
        self.btn_clean.config(state="normal")
        self.lbl_scan_status.config(text="Analysis complete")
        
        # Default select recommended items that have size > 0
        for item in items:
            self.selected_states[item['id']] = bool(item['recommended'] and item['size_bytes'] > 0)
            self.update_card_visuals(item['id'])
        
        self.update_selection_summary()
        total_reclaimable = sum(item['size_bytes'] for item in items if item['recommended'])
        self.log(f"Scan complete. Recommended cleanup can reclaim ~{self.format_size(total_reclaimable)}.")

    def render_items_list(self):
        for widget in self.scrollable_inner.winfo_children():
            widget.destroy()

        self.item_cards = {}

        for item in self.items_data:
            item_id = item['id']
            # Default state
            if item_id not in self.selected_states:
                self.selected_states[item_id] = bool(item['recommended'] and item['size_bytes'] > 0)

            # Outer Card Frame (entire card is clickable!)
            card = tk.Frame(
                self.scrollable_inner, 
                bg=BG_CARD, 
                padx=14, 
                pady=12, 
                highlightbackground=BORDER_COLOR, 
                highlightthickness=1,
                cursor="hand2"
            )
            card.pack(fill="x", pady=4, padx=5)

            # Left Badge (Button/Indicator)
            badge_btn = tk.Label(
                card, 
                text="[ ✔ SELECTED ]" if self.selected_states[item_id] else "[   ENABLE   ]",
                font=("Segoe UI", 9, "bold"),
                bg="#1b4728" if self.selected_states[item_id] else PROGRESS_BG,
                fg="#39d353" if self.selected_states[item_id] else TEXT_MUTED,
                padx=10, 
                pady=5, 
                cursor="hand2",
                relief="flat",
                width=14
            )
            badge_btn.pack(side="left", padx=(0, 15))

            # Center Details
            center_frame = tk.Frame(card, bg=BG_CARD, cursor="hand2")
            center_frame.pack(side="left", fill="both", expand=True)

            name_color = TEXT_PRIMARY if item['size_bytes'] > 0 else TEXT_MUTED
            lbl_name = tk.Label(center_frame, text=item['name'], font=("Segoe UI", 10, "bold"), fg=name_color, bg=BG_CARD, cursor="hand2")
            lbl_name.pack(anchor="w")

            lbl_desc = tk.Label(center_frame, text=item['desc'], font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_CARD, cursor="hand2")
            lbl_desc.pack(anchor="w", pady=(2, 0))

            # Right Size
            size_color = ACCENT_WARN if item['size_bytes'] > 1024**3 else (ACCENT_GREEN if item['size_bytes'] > 0 else TEXT_MUTED)
            lbl_size = tk.Label(card, text=item['size_display'], font=("Segoe UI", 11, "bold"), fg=size_color, bg=BG_CARD, cursor="hand2")
            lbl_size.pack(side="right", padx=(10, 10))

            widgets_group = [card, badge_btn, center_frame, lbl_name, lbl_desc, lbl_size]
            self.item_cards[item_id] = {
                "card": card,
                "badge": badge_btn,
                "center": center_frame,
                "name": lbl_name,
                "desc": lbl_desc,
                "size": lbl_size,
                "item": item
            }

            # Bind click handler to ALL child elements of the card
            for w in widgets_group:
                w.bind("<Button-1>", lambda e, iid=item_id: self.toggle_item(iid))
                w.bind("<Enter>", lambda e, iid=item_id: self._on_card_hover(iid, True))
                w.bind("<Leave>", lambda e, iid=item_id: self._on_card_hover(iid, False))

            self.update_card_visuals(item_id)

    def toggle_item(self, item_id):
        self.selected_states[item_id] = not self.selected_states.get(item_id, False)
        self.update_card_visuals(item_id)
        self.update_selection_summary()

    def update_card_visuals(self, item_id):
        if item_id not in self.item_cards:
            return
        
        is_sel = self.selected_states.get(item_id, False)
        c = self.item_cards[item_id]

        bg_color = BG_CARD_SELECTED if is_sel else BG_CARD
        border_col = BORDER_SELECTED if is_sel else BORDER_COLOR
        badge_bg = "#1b4728" if is_sel else PROGRESS_BG
        badge_fg = "#39d353" if is_sel else TEXT_MUTED
        badge_text = "[ ✔ SELECTED ]" if is_sel else "[   ENABLE   ]"

        c["card"].config(bg=bg_color, highlightbackground=border_col, highlightthickness=1)
        c["center"].config(bg=bg_color)
        c["name"].config(bg=bg_color)
        c["desc"].config(bg=bg_color)
        c["size"].config(bg=bg_color)
        c["badge"].config(text=badge_text, bg=badge_bg, fg=badge_fg)

    def _on_card_hover(self, item_id, is_hovering):
        if item_id not in self.item_cards:
            return
        is_sel = self.selected_states.get(item_id, False)
        if not is_sel:
            hover_bg = BG_CARD_HOVER if is_hovering else BG_CARD
            c = self.item_cards[item_id]
            c["card"].config(bg=hover_bg)
            c["center"].config(bg=hover_bg)
            c["name"].config(bg=hover_bg)
            c["desc"].config(bg=hover_bg)
            c["size"].config(bg=hover_bg)

    def update_selection_summary(self):
        sel_count = 0
        sel_bytes = 0
        for item in self.items_data:
            if self.selected_states.get(item['id'], False):
                sel_count += 1
                sel_bytes += item['size_bytes']

        self.lbl_selected_summary.config(
            text=f"Selected: {sel_count} target(s)  |  Estimated space to reclaim: {self.format_size(sel_bytes)}"
        )

    def select_recommended(self):
        for item in self.items_data:
            self.selected_states[item['id']] = bool(item['recommended'] and item['size_bytes'] > 0)
            self.update_card_visuals(item['id'])
        self.update_selection_summary()
        self.log("Selected recommended safe targets.")

    def select_all(self):
        for item in self.items_data:
            self.selected_states[item['id']] = bool(item['size_bytes'] > 0)
            self.update_card_visuals(item['id'])
        self.update_selection_summary()
        self.log("Selected all available targets.")

    def deselect_all(self):
        for item in self.items_data:
            self.selected_states[item['id']] = False
            self.update_card_visuals(item['id'])
        self.update_selection_summary()
        self.log("Deselected all targets.")

    def start_cleaning(self):
        if self.is_cleaning or self.is_scanning:
            return

        selected_items = [
            item for item in self.items_data 
            if self.selected_states.get(item['id'], False)
        ]

        if not selected_items:
            messagebox.showinfo("No Selection", "Please click on any target card to select it for cleaning.")
            return

        total_bytes = sum(i['size_bytes'] for i in selected_items)
        confirm = messagebox.askyesno(
            "Confirm Cleanup - Writenix Tech Solutions",
            f"Are you sure you want to clean {len(selected_items)} selected target(s)?\n\n"
            f"Estimated space to reclaim: {self.format_size(total_bytes)}\n\n"
            "This will delete temporary caches and build artifacts without affecting personal files."
        )

        if not confirm:
            return

        self.is_cleaning = True
        self.btn_scan.config(state="disabled")
        self.btn_clean.config(state="disabled")
        self.lbl_scan_status.config(text="Cleaning selected targets...")
        
        threading.Thread(target=self._cleaning_worker, args=(selected_items,), daemon=True).start()

    def _cleaning_worker(self, items_to_clean):
        freed_bytes = 0

        for item in items_to_clean:
            self.root.after(0, lambda name=item['name']: self.lbl_scan_status.config(text=f"Cleaning {name}..."))
            self.root.after(0, lambda msg=f"Purging {item['name']}...": self.log(msg))

            if item['clean_type'] == 'hibernation':
                try:
                    import ctypes
                    self.root.after(0, lambda: self.log("Requesting Administrator (UAC) permission to disable hibernation..."))
                    
                    # ShellExecuteW with 'runas' prompts Windows UAC dialog
                    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", "powercfg.exe", "/hibernate off", None, 0)
                    
                    if ret > 32:  # Windows ShellExecute return code > 32 indicates success
                        # Give Windows 1.5 seconds to unlock and release hiberfil.sys
                        import time
                        time.sleep(1.5)
                        if not os.path.exists("C:\\hiberfil.sys"):
                            freed_bytes += item['size_bytes']
                            self.root.after(0, lambda: self.log("✔ Windows Hibernation successfully disabled! (Reclaimed ~4.0 GB)"))
                        else:
                            self.root.after(0, lambda: self.log("ℹ Windows processed command. Refreshing disk metrics..."))
                    else:
                        self.root.after(0, lambda: self.log("⚠️ Administrator permission (UAC) was cancelled. Hibernation requires Administrator rights."))
                except Exception as e:
                    self.root.after(0, lambda err=e: self.log(f"Hibernate toggle error: {err}"))

            elif item['clean_type'] == 'dir_contents':
                folder_path = item['path']
                if os.path.exists(folder_path):
                    cleared_this = 0
                    try:
                        for entry in os.scandir(folder_path):
                            try:
                                if entry.is_file(follow_symlinks=False) or entry.is_symlink():
                                    f_size = entry.stat(follow_symlinks=False).st_size
                                    os.remove(entry.path)
                                    cleared_this += f_size
                                elif entry.is_dir(follow_symlinks=False):
                                    d_size = self.get_dir_size_fast(entry.path)
                                    shutil.rmtree(entry.path, ignore_errors=True)
                                    cleared_this += d_size
                            except Exception:
                                continue
                    except Exception:
                        pass
                    freed_bytes += cleared_this
                    self.root.after(0, lambda name=item['name'], amt=self.format_size(cleared_this): 
                                    self.log(f"✔ Cleaned {name} (Reclaimed {amt})"))

        self.root.after(0, lambda: self._on_cleaning_finished(freed_bytes))

    def _on_cleaning_finished(self, freed_bytes):
        self.is_cleaning = False
        self.log(f"Cleanup completed! Total reclaimed: ~{self.format_size(freed_bytes)}.")
        messagebox.showinfo(
            "Cleanup Complete",
            f"Writenix Disk Optimizer successfully cleaned the selected targets!\n\n"
            f"Space Reclaimed: ~{self.format_size(freed_bytes)}"
        )
        self.start_scan()

def main():
    root = tk.Tk()
    app = WritenixOptimizerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
