import os
import subprocess
import requests
import zipfile


def xor_enc(s, keys):
    """Encrypts a string using XOR with a 4-byte key."""
    return "".join([f"\\x{ord(s[i]) ^ keys[i % 4]:02x}" for i in range(len(s))])

def check_compiler(log_callback):
    """Checks for GCC in system PATH or local folder."""
    # 1. Check system PATH
    try:
        subprocess.run(["gcc", "--version"], capture_output=True, check=True)
        log_callback("[+] GCC Compiler is ready (System).")
        return True
    except:
        pass

    # 2. Check local folder
    local_gcc = os.path.join(os.getcwd(), "compiler", "w64devkit", "bin")
    if os.path.exists(local_gcc):
        os.environ["PATH"] += os.pathsep + local_gcc
        log_callback("[+] Found local compiler, added to PATH.")
        return True

    # 3. Download if not found
    log_callback("[!] GCC not found. Downloading w64devkit...")
    return download_mingw(log_callback)

def download_mingw(log_callback):
    """Downloads and extracts the w64devkit compiler."""
    try:
        url = "https://github.com/skeeto/w64devkit/releases/download/v1.23.0/w64devkit-1.23.0.zip"
        r = requests.get(url, stream=True)
        with open("compiler.zip", "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        
        if not os.path.exists("compiler"):
            os.makedirs("compiler")
            
        with zipfile.ZipFile("compiler.zip", 'r') as z:
            z.extractall("compiler")
            
        os.environ["PATH"] += os.pathsep + os.path.join(os.getcwd(), "compiler", "w64devkit", "bin")
        os.remove("compiler.zip")
        log_callback("[+] Compiler setup finished!")
        return True
    except Exception as e:
        log_callback(f"[-] Compiler error: {e}")
        return False
