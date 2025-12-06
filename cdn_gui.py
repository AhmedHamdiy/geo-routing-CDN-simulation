import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
import time
from data.users import USERS_IPS
from data.edge_endpoints import EDGE_ENDPOINTS
import geoDNS_resolver


class CDNVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("CDN Demo Visualizer")
        self.root.geometry("1400x900")
        self.root.configure(bg="#1e1e1e")
        
        self.colors = {
            "bg": "#1e1e1e",
            "origin": "#ff6b6b",
            "edge": "#4ecdc4",
            "user": "#95e1d3",
            "arrow_hit": "#51cf66",
            "arrow_miss": "#ff6b6b",
            "text": "#ffffff",
            "panel": "#2d2d2d"
        }
        
        self.animations = []
        self.animation_running = False
        
        self.setup_network_topology()
        
        self.create_ui()
        
    def setup_network_topology(self):
        self.origin = {
            "name": "Origin Server",
            "port": "8080",
            "location": "Main Data Center",
            "x": 500,
            "y": 100,
            "width": 120,
            "height": 80,
            "color": self.colors["origin"]
        }
        
        self.edges = {
            "US-EAST": {
                "name": "US-EAST (edge1)",
                "port": "8081",
                "location": "New York, USA",
                "x": 300,
                "y": 350,
                "width": 120,
                "height": 80,
                "color": self.colors["edge"],
                "endpoint": "http://localhost:8081"
            },
            "EU-WEST": {
                "name": "EU-WEST (edge2)",
                "port": "8082",
                "location": "Paris, France",
                "x": 700,
                "y": 350,
                "width": 120,
                "height": 80,
                "color": self.colors["edge"],
                "endpoint": "http://localhost:8082"
            }
        }
        
        self.users = {}
        region_x_positions = {
            "US-EAST": 300,
            "AFRICA-NORTH": 500,
            "EU-WEST": 700
        }
        
        region_counts = {}
        for ip, info in USERS_IPS.items():
            region = info["region"]
            if region not in region_counts:
                region_counts[region] = 0
            
            base_x = region_x_positions.get(region, 700)
            offset_x = (region_counts[region] % 2) * 80 - 10
            offset_y = (region_counts[region] // 2) * 70
            
            self.users[ip] = {
                "name": info["location_name"],
                "region": region,
                "ip": ip,
                "x": base_x + offset_x,
                "y": 600 + offset_y,
                "width": 60,
                "height": 60,
                "color": self.colors["user"]
            }
            
            region_counts[region] += 1
    
    def create_ui(self):
        self.canvas = tk.Canvas(
            self.root,
            bg=self.colors["bg"],
            highlightthickness=0
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.create_control_panel()
        
        self.draw_network()
        
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
    def create_control_panel(self):
        panel = tk.Frame(self.root, bg=self.colors["panel"], width=300)
        panel.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        panel.pack_propagate(False)
        
        title = tk.Label(
            panel,
            text="CDN Control Panel",
            font=("Arial", 16, "bold"),
            bg=self.colors["panel"],
            fg=self.colors["text"]
        )
        title.pack(pady=20)
        
        info_label = tk.Label(
            panel,
            text="Server Info:",
            font=("Arial", 12, "bold"),
            bg=self.colors["panel"],
            fg=self.colors["text"],
            anchor="w"
        )
        info_label.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        self.info_text = tk.Text(
            panel,
            height=10,
            bg="#3d3d3d",
            fg=self.colors["text"],
            font=("Consolas", 10),
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.info_text.pack(fill=tk.X, padx=10, pady=5)
        self.info_text.insert("1.0", "Click on a server to view details")
        self.info_text.config(state=tk.DISABLED)
        
        user_label = tk.Label(
            panel,
            text="Select User:",
            font=("Arial", 12, "bold"),
            bg=self.colors["panel"],
            fg=self.colors["text"],
            anchor="w"
        )
        user_label.pack(fill=tk.X, padx=10, pady=(20, 0))
        
        self.user_var = tk.StringVar()
        user_options = [f"{info['location_name']} ({ip})" for ip, info in USERS_IPS.items()]
        self.user_dropdown = ttk.Combobox(
            panel,
            textvariable=self.user_var,
            values=user_options,
            state="readonly",
            font=("Arial", 9)
        )
        self.user_dropdown.pack(fill=tk.X, padx=10, pady=5)
        if user_options:
            self.user_dropdown.current(0)
        
        btn_frame = tk.Frame(panel, bg=self.colors["panel"])
        btn_frame.pack(fill=tk.X, padx=10, pady=20)
        
        self.request_btn = tk.Button(
            btn_frame,
            text="Send Request",
            command=self.send_request,
            bg="#4ecdc4",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            height=2
        )
        self.request_btn.pack(fill=tk.X, pady=5)
        
        self.auto_test_btn = tk.Button(
            btn_frame,
            text="Run Auto Test (All Users)",
            command=self.run_auto_test,
            bg="#4ecdc4",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            height=2
        )
        self.auto_test_btn.pack(fill=tk.X, pady=5)
        
        log_label = tk.Label(
            panel,
            text="Request Log:",
            font=("Arial", 12, "bold"),
            bg=self.colors["panel"],
            fg=self.colors["text"],
            anchor="w"
        )
        log_label.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        log_frame = tk.Frame(panel, bg=self.colors["panel"])
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = tk.Scrollbar(log_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(
            log_frame,
            height=15,
            bg="#3d3d3d",
            fg=self.colors["text"],
            font=("Consolas", 9),
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=10,
            pady=10,
            yscrollcommand=scrollbar.set
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)
        
        clear_btn = tk.Button(
            panel,
            text="Clear Log",
            command=self.clear_log,
            bg="#6c757d",
            fg="white",
            font=("Arial", 9),
            relief=tk.FLAT,
            cursor="hand2"
        )
        clear_btn.pack(fill=tk.X, padx=10, pady=5)
        
    def draw_network(self):
        self.draw_connections()
        
        self.draw_server(self.origin, "origin")
        
        for region, edge in self.edges.items():
            self.draw_server(edge, f"edge_{region}")
        
        for ip, user in self.users.items():
            self.draw_user(user, ip)
        
    
    def draw_connections(self):
        for region, edge in self.edges.items():
            self.canvas.create_line(
                self.origin["x"] + self.origin["width"] // 2, self.origin["y"] + self.origin["height"],
                edge["x"] + edge["width"] // 2, edge["y"],
                fill="#404040",
                width=2,
                dash=(5, 5),
                tags="connection"
            )
        
        for ip, user in self.users.items():
            user_location = USERS_IPS[ip]["location_name"]
            if "Tanta" in user_location:
                self.canvas.create_line(
                    self.origin["x"] + self.origin["width"] // 2, self.origin["y"] + self.origin["height"],
                    user["x"] + user["width"] // 2, user["y"],
                    fill="#404040",
                    width=2,
                    dash=(3, 3),
                    tags="connection"
                )
            else:
                edge = self.edges.get(user["region"])
                if edge:
                    self.canvas.create_line(
                        edge["x"] + edge["width"] // 2, edge["y"] + edge["height"],
                        user["x"] + user["width"] // 2, user["y"],
                        fill="#404040",
                        width=1,
                        dash=(3, 3),
                        tags="connection"
                    )
    
    def draw_server(self, server, tag):
        x, y = server["x"], server["y"]
        w, h = server["width"], server["height"]
        
        self.canvas.create_rectangle(
            x + 5, y + 5, x + w + 5, y + h + 5,
            fill="#000000",
            outline="",
            tags=(tag, "shadow")
        )
        
        rect = self.canvas.create_rectangle(
            x, y, x + w, y + h,
            fill=server["color"],
            outline="#ffffff",
            width=2,
            tags=(tag, "server", "clickable")
        )
        
        self.canvas.create_text(
            x + w // 2, y + h // 2,
            text=server["name"],
            fill="white",
            font=("Arial", 10, "bold"),
            tags=(tag, "server_text"),
            width=w - 10
        )
        
        self.canvas.tag_bind(rect, "<Enter>", lambda e, s=server: self.on_server_hover(e, s))
        self.canvas.tag_bind(rect, "<Leave>", lambda e: self.on_server_leave(e))
    
    def draw_user(self, user, tag):
        x, y = user["x"], user["y"]
        w, h = user["width"], user["height"]
        
        oval = self.canvas.create_oval(
            x, y, x + w, y + h,
            fill=user["color"],
            outline="#ffffff",
            width=2,
            tags=(tag, "user", "clickable")
        )
        
        icon = self.canvas.create_text(
            x + w // 2 , y + h // 2 - 4,
            text="💻",
            font=("Arial", 26),
            tags=(tag, "user_icon", "clickable")
        )
        
        self.canvas.create_text(
            x + w // 2, y + h + 15,
            text=user["name"].split(",")[0],
            fill=self.colors["text"],
            font=("Arial", 8),
            tags=(tag, "user_label")
        )
        
        # Bind hover and click events
        self.canvas.tag_bind(oval, "<Enter>", lambda e: self.on_user_hover(e))
        self.canvas.tag_bind(oval, "<Leave>", lambda e: self.on_user_leave(e))
        self.canvas.tag_bind(icon, "<Enter>", lambda e: self.on_user_hover(e))
        self.canvas.tag_bind(icon, "<Leave>", lambda e: self.on_user_leave(e))
    
    def on_server_hover(self, event, server):
        self.canvas.config(cursor="hand2")
    
    def on_server_leave(self, event):
        self.canvas.config(cursor="")
    
    def on_user_hover(self, event):
        self.canvas.config(cursor="hand2")
    
    def on_user_leave(self, event):
        self.canvas.config(cursor="")
    
    def on_canvas_click(self, event):
        clicked_items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        
        for item in clicked_items:
            tags = self.canvas.gettags(item)
            
            if "origin" in tags:
                self.show_server_info(self.origin, "Origin")
                return
            
            for region, edge in self.edges.items():
                if f"edge_{region}" in tags:
                    self.show_server_info(edge, f"Edge - {region}")
                    return
            
            # Check if a user device was clicked
            for user_ip in self.users.keys():
                if user_ip in tags:
                    self.select_user(user_ip)
                    return
    
    def show_server_info(self, server, server_type):
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        
        info = f"{server_type} Information\n"
        info += "=" * 30 + "\n\n"
        info += f"Name: {server['name']}\n"
        info += f"Port: {server['port']}\n"
        info += f"Location: {server['location']}\n"
        
        if "endpoint" in server:
            info += f"Endpoint: {server['endpoint']}\n"
        
        self.info_text.insert("1.0", info)
        self.info_text.config(state=tk.DISABLED)
    
    def select_user(self, user_ip):
        """Select a user in the dropdown when their device is clicked"""
        user_info = USERS_IPS[user_ip]
        selection_text = f"{user_info['location_name']} ({user_ip})"
        self.user_var.set(selection_text)
        
        # Flash the selected user device
        user = self.users[user_ip]
        x, y = user["x"], user["y"]
        w, h = user["width"], user["height"]
        
        # Create a highlight effect
        highlight = self.canvas.create_oval(
            x - 5, y - 5, x + w + 5, y + h + 5,
            outline="#ffd700",
            width=3,
            tags="highlight"
        )
        self.root.after(500, lambda: self.canvas.delete(highlight))
    
    def log_message(self, message, color="white"):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def clear_log(self):
        self.log_text.delete("1.0", tk.END)
    
    def get_selected_user_ip(self):
        selected = self.user_var.get()
        if not selected:
            return None
        ip = selected.split("(")[-1].strip(")")
        return ip
    
    def send_request(self):
        user_ip = self.get_selected_user_ip()
        if not user_ip:
            messagebox.showwarning("No User Selected", "Please select a user device first.")
            return
        
        self.log_message(f"\n📤 Sending request from {USERS_IPS[user_ip]['location_name']}")
        threading.Thread(target=self.process_request, args=(user_ip,), daemon=True).start()

    def process_request(self, user_ip):
        user = self.users[user_ip]
        user_location = USERS_IPS[user_ip]["location_name"]
        
        if "Tanta" in user_location:
            endpoint = "http://localhost:8080"
            cache_status, latency, edge_server, status_code = self.make_http_request(user_ip, endpoint)
            is_miss = False
            edge_server = "Origin Server"
            self.animate_request(user_ip, is_miss, latency, edge_server, status_code, is_origin=True)
        else:
            edge = self.edges[user["region"]]
            cache_status, latency, edge_server, status_code = self.make_http_request(user_ip, edge["endpoint"])
            is_miss = (cache_status or "").upper() != "HIT"
            self.animate_request(user_ip, is_miss, latency, edge_server, status_code, is_origin=False)
    
    def animate_request(self, user_ip, is_miss, latency, edge_server, status_code, is_origin=False):
        user = self.users[user_ip]
        region = user["region"]
        
        if is_origin:
            self.draw_animated_arrow(
                user["x"] + user["width"] // 2,
                user["y"],
                self.origin["x"] + self.origin["width"] // 2,
                self.origin["y"] + self.origin["height"],
                self.colors["arrow_miss"],
                "Request to Origin"
            )
            
            # Origin to User (response)
            time.sleep(0.5)
            self.draw_animated_arrow(
                self.origin["x"] + self.origin["width"] // 2,
                self.origin["y"] + self.origin["height"],
                user["x"] + user["width"] // 2,
                user["y"],
                self.colors["arrow_miss"],
                "Origin Response"
            )
        else:
            # Normal edge server flow
            edge = self.edges[region]
            
            # User to Edge
            self.draw_animated_arrow(
                user["x"] + user["width"] // 2,
                user["y"],
                edge["x"] + edge["width"] // 2,
                edge["y"] + edge["height"],
                self.colors["arrow_miss"] if is_miss else self.colors["arrow_hit"],
                "Request"
            )
            
            if is_miss:
                # Edge to Origin (cache miss)
                time.sleep(0.5)
                self.draw_animated_arrow(
                    edge["x"] + edge["width"] // 2,
                    edge["y"],
                    self.origin["x"]+ self.origin["width"] // 2,
                    self.origin["y"] + self.origin["height"],
                    self.colors["arrow_miss"],
                    "Fetch from Origin"
                )
                
                # Origin to Edge (response)
                time.sleep(0.5)
                self.draw_animated_arrow(
                    self.origin["x"] + self.origin["width"] // 2,
                    self.origin["y"] + self.origin["height"],
                    edge["x"] + edge["width"] // 2,
                    edge["y"],
                    self.colors["arrow_miss"],
                    "Origin Response"
                )
            
            # Edge to User (response)
            time.sleep(0.5)
            self.draw_animated_arrow(
                edge["x"] + edge["width"] // 2,
                edge["y"] + edge["height"],
                user["x"] + user["width"] // 2,
                user["y"],
                self.colors["arrow_hit"],
                "Response"
            )
        
        time.sleep(0.5)
        self.log_request(is_miss, latency, edge_server, status_code, is_origin)
        
    
    def draw_animated_arrow(self, x1, y1, x2, y2, color, label):
        arrow = self.canvas.create_line(
            x1, y1, x2, y2,
            fill=color,
            width=4,
            arrow=tk.LAST,
            arrowshape=(16, 20, 6),
            tags="animation"
        )
        
        mid_x, mid_y = (x1 + x2) // 2, (y1 + y2) // 2
        text = self.canvas.create_text(
            mid_x, mid_y - 15,
            text=label,
            fill=color,
            font=("Arial", 10, "bold"),
            tags="animation"
        )
        
        self.root.after(500, lambda: self.canvas.delete(arrow))
        self.root.after(500, lambda: self.canvas.delete(text))
    
    def make_http_request(self, user_ip, edge_url):
        try:
            start_time = time.time()
            response = requests.get(edge_url, timeout=5)
            end_time = time.time()
            
            latency = (end_time - start_time) * 1000
            cache_status = response.headers.get('X-Cache-Status', 'N/A')
            edge_server = response.headers.get('X-Edge-Server', 'N/A')
            return cache_status, latency, edge_server, response.status_code
            
        except Exception as e:
            self.log_message(f"  ✗ Request failed: {str(e)}", "red")
            return 'N/A', 0, 'N/A', 500
    
    def log_request(self, is_missed, latency, edge_server, status_code, is_origin=False):
        self.log_message(f"  ✓ Status: {status_code}")
        self.log_message(f"  ✓ Edge Server: {edge_server}")
        self.log_message(f"  ✓ Latency: {latency:.2f} ms")
        # Only display cache status if user is not directly connected to origin
        if not is_origin:
            self.log_message(f"  ✓ Cache Status: {'MISS' if is_missed else 'HIT'}")

    def run_auto_test(self):
        self.log_message("\n" + "="*50)
        self.log_message("🚀 Starting Automated Test for All Users")
        self.log_message("="*50)
        
        threading.Thread(target=self._auto_test_worker, daemon=True).start()
    
    def _auto_test_worker(self):
        for user_ip, user_info in USERS_IPS.items():
            self.log_message(f"\n👤 Testing: {user_info['location_name']}")
            
            self.log_message("  📤 Request")
            self.process_request(user_ip)
            time.sleep(1.5)
        
        self.log_message("\n✅ Automated test completed!")


def main():
    root = tk.Tk()
    app = CDNVisualizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
