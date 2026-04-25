# Basic-C-Bot-net

Basic-C-Bot-net is an advanced All-In-One tool designed for educational purposes and security research. It features a powerful payload builder with stealth capabilities and a Command & Control (C&C) server for managing remote agents.

## ✨ Features

- **Advanced Builder**: Generate highly customized EXE or DLL payloads.
- **Stealth Logic**:
  - Auto-persistence via Registry.
  - Multiple drop locations (AppData, LocalAppData, Temp, Startup).
  - Anti-Sandboxing (TickCount delay).
  - Hidden and System file attributes.
  - Self-deletion of the original file after execution.
- **C&C Server**:
  - Real-time agent monitoring.
  - Multi-agent command execution.
  - Quick DOS attack panel (UDP Flood).
  - Remote update and kill switch functionality.
- **Modern UI**: Built with `customtkinter` for a sleek, responsive experience.
- **Auto-Compiler Setup**: Automatically detects or downloads the `w64devkit` (GCC) compiler for seamless payload generation.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Windows OS (for building and running payloads)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/gemini-aio.git
   cd gemini-aio
   ```

2. Install dependencies:
   ```bash
   pip install customtkinter pycryptodome requests
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## 🛠 Usage

1. **Builder Tab**: 
   - Enter your C2 Server IP and Port.
   - Choose the file type (EXE or DLL).
   - Configure stealth options and click **GENERATE PAYLOAD**.
2. **C&C Tab**:
   - Click **START CNC SERVER** to begin listening for connections.
   - Manage connected agents and send commands using the panels provided.

## ⚠️ Disclaimer

This tool is for **educational and ethical security testing only**. The developer is not responsible for any misuse or damage caused by this software. Use it only on systems you own or have explicit permission to test.

## 📜 License

This project is licensed under the [MIT License](LICENSE).
