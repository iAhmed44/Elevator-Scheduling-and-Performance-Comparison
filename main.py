#For windows pip install psutil
#For MacOS use resource module 
import random
import tkinter as tk
import time
from dataclasses import dataclass
from typing import List, Tuple, Optional
import sys
import os
import threading

# --- CROSS-PLATFORM MEMORY IMPORT ---
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
# ------------------------------------

FLOOR_MAP = {'A': 1, 'B': 2, 'C': 3, 'D': 4}
REV_MAP = {v: k for k, v in FLOOR_MAP.items()}

@dataclass
class Request:
    start: int
    dest: int
    gen_time: float = 0.0
    id: int = 0

class ElevatorSimulatorBoth:
    def __init__(self, master, max_requests: Optional[int] = None):
        self.master = master
        master.title("Elevator Simulation – FCFS & LOOK with Real-time Generation")

        # Make max_requests optional (defaults to 25 if not provided)
        self.max_requests = max_requests if max_requests is not None else 25

        # Request state - NO PRE-GENERATION
        self.request_pairs = []
        self.requests_numeric: List[Request] = [] 
        self.fcfs_states = []
        self.look_states = []

        # Generation
        self.generated = 0
        self.generating = False
        self.next_request_id = 1
        self.generation_interval = 400  # 0.4 seconds = 400ms
        self.floor_move_interval = 200  # 0.2 seconds = 200ms per floor

        # FCFS
        self.fcfs_floor = 1
        self.fcfs_index = 0
        self.fcfs_phase = "to_start"
        self.fcfs_distance = 0
        self.fcfs_steps = 0
        self.fcfs_running = False
        self.fcfs_start_time = 0.0
        self.fcfs_time = 0.0
        self.fcfs_wait_times: List[float] = [] 
        self.total_pickups_fcfs = 0 
        self.fcfs_operations = 0

        # LOOK
        self.look_floor = 1
        self.look_direction = 0
        self.look_distance = 0
        self.look_steps = 0
        self.look_running = False
        self.look_start_time = 0.0
        self.look_time = 0.0
        self.look_wait_times: List[float] = []
        self.total_pickups_look = 0
        self.look_operations = 0

        # CPU Utilization tracking
        self.cpu_samples_fcfs = []
        self.cpu_samples_look = []
        self.monitoring_cpu = False
        
        # Baseline Memory Usage
        self.baseline_memory_mb = self.get_current_memory_mb()

        # LEFT PANEL
        left = tk.Frame(master, padx=10, pady=10)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ## Configuration Input
        config_frame = tk.Frame(left)
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(config_frame, text="Number of Requests (n):", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 5))
        self.n_input = tk.Entry(config_frame, width=10)
        self.n_input.insert(0, str(self.max_requests))
        self.n_input.pack(side=tk.LEFT, padx=(0, 10))
        
        self.config_label = tk.Label(config_frame, text=f"Current: {self.max_requests}", 
                                      font=('Arial', 9), fg='blue')
        self.config_label.pack(side=tk.LEFT)

        # Timing info
        timing_frame = tk.Frame(left)
        timing_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(timing_frame, text="⏱ Order interval: 0.4s | Floor move: 0.2s", 
                 font=('Arial', 9), fg='gray').pack()

        ## 1. Request List
        tk.Label(left, text="Real-time Elevator Requests", font=('Arial', 10, 'bold')).pack(fill=tk.X)
        
        # Frame for listbox with scrollbar
        list_frame = tk.Frame(left)
        list_frame.pack(fill=tk.X, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.all_requests_list = tk.Listbox(list_frame, height=8, yscrollcommand=scrollbar.set)
        self.all_requests_list.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scrollbar.config(command=self.all_requests_list.yview)

        ## 2. Comparison Area
        tk.Label(left, text="FCFS vs LOOK Comparison", font=('Arial', 12, 'bold')).pack(fill=tk.X, pady=(10, 5))

        comp_frame = tk.Frame(left, relief=tk.GROOVE, borderwidth=2)
        comp_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        tk.Label(comp_frame, text="Metric", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky="nsew", padx=5, pady=2)
        tk.Label(comp_frame, text="FCFS", font=('Arial', 10, 'bold'), bg='skyblue').grid(row=0, column=1, sticky="nsew", padx=5, pady=2)
        tk.Label(comp_frame, text="LOOK", font=('Arial', 10, 'bold'), bg='lightgreen').grid(row=0, column=2, sticky="nsew", padx=5, pady=2)

        # Metrics Rows
        row = 1
        
        # Execution Time (ms)
        tk.Label(comp_frame, text="Execution Time (ms)").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.comp_time_ms_fcfs = tk.Label(comp_frame, text="0 ms")
        self.comp_time_ms_fcfs.grid(row=row, column=1, sticky="e", padx=5, pady=2)
        self.comp_time_ms_look = tk.Label(comp_frame, text="0 ms")
        self.comp_time_ms_look.grid(row=row, column=2, sticky="e", padx=5, pady=2)
        row += 1
        
        # Memory Usage
        tk.Label(comp_frame, text="Memory Usage (MB)").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.comp_memory = tk.Label(comp_frame, text="Running...") 
        self.comp_memory.grid(row=row, column=1, sticky="e", padx=5, pady=2, columnspan=2)
        row += 1
        
        # Throughput
        tk.Label(comp_frame, text="Throughput (ops/s)").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.comp_throughput_fcfs = tk.Label(comp_frame, text="0.00")
        self.comp_throughput_fcfs.grid(row=row, column=1, sticky="e", padx=5, pady=2)
        self.comp_throughput_look = tk.Label(comp_frame, text="0.00")
        self.comp_throughput_look.grid(row=row, column=2, sticky="e", padx=5, pady=2)
        row += 1
        
        # Average Waiting Time
        tk.Label(comp_frame, text="Avg Wait Time (s)").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.comp_wait_fcfs = tk.Label(comp_frame, text="0.00s")
        self.comp_wait_fcfs.grid(row=row, column=1, sticky="e", padx=5, pady=2)
        self.comp_wait_look = tk.Label(comp_frame, text="0.00s")
        self.comp_wait_look.grid(row=row, column=2, sticky="e", padx=5, pady=2)
        row += 1
        
        # CPU Utilization
        tk.Label(comp_frame, text="CPU Utilization (%)").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.comp_cpu_fcfs = tk.Label(comp_frame, text="0.00%")
        self.comp_cpu_fcfs.grid(row=row, column=1, sticky="e", padx=5, pady=2)
        self.comp_cpu_look = tk.Label(comp_frame, text="0.00%")
        self.comp_cpu_look.grid(row=row, column=2, sticky="e", padx=5, pady=2)
        row += 1
        
        # Steps
        tk.Label(comp_frame, text="Steps").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.comp_steps_fcfs = tk.Label(comp_frame, text="0")
        self.comp_steps_fcfs.grid(row=row, column=1, sticky="e", padx=5, pady=2)
        self.comp_steps_look = tk.Label(comp_frame, text="0")
        self.comp_steps_look.grid(row=row, column=2, sticky="e", padx=5, pady=2)
        row += 1

        # Distance
        tk.Label(comp_frame, text="Distance").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.comp_dist_fcfs = tk.Label(comp_frame, text="0")
        self.comp_dist_fcfs.grid(row=row, column=1, sticky="e", padx=5, pady=2)
        self.comp_dist_look = tk.Label(comp_frame, text="0")
        self.comp_dist_look.grid(row=row, column=2, sticky="e", padx=5, pady=2)
        row += 1

        # Completed Requests
        tk.Label(comp_frame, text="Completed Requests").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.comp_completed_fcfs = tk.Label(comp_frame, text="0")
        self.comp_completed_fcfs.grid(row=row, column=1, sticky="e", padx=5, pady=2)
        self.comp_completed_look = tk.Label(comp_frame, text="0")
        self.comp_completed_look.grid(row=row, column=2, sticky="e", padx=5, pady=2)

        comp_frame.grid_columnconfigure(0, weight=1)
        comp_frame.grid_columnconfigure(1, weight=1)
        comp_frame.grid_columnconfigure(2, weight=1)

        # RIGHT PANEL
        right = tk.Frame(master, padx=10, pady=10)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(right, width=300, height=400, bg="white")
        self.canvas.pack()

        self.floor_y = {}
        margin_top = 40
        margin_bottom = 40
        usable = 400 - margin_top - margin_bottom

        for f in range(1, 5):
            rel = (f - 1) / 3
            y = 400 - margin_bottom - usable * rel
            self.floor_y[f] = y
            self.canvas.create_line(40, y, 260, y)
            self.canvas.create_text(20, y, text=REV_MAP[f], font=('Arial', 10, 'bold'))

        # FCFS elevator
        y_fcfs = self.floor_y[self.fcfs_floor]
        self.elev_fcfs = self.canvas.create_rectangle(80, y_fcfs - 15, 120, y_fcfs + 15, fill="skyblue")
        self.canvas.create_text(100, 20, text="FCFS", font=('Arial', 10, 'bold'))

        # LOOK elevator
        y_look = self.floor_y[self.look_floor]
        self.elev_look = self.canvas.create_rectangle(160, y_look - 15, 200, y_look + 15, fill="lightgreen")
        self.canvas.create_text(200, 20, text="LOOK", font=('Arial', 10, 'bold'))

        # Button Panel
        button_panel = tk.Frame(right)
        button_panel.pack(pady=10)
        self.start_button = tk.Button(button_panel, text="Start Simulation", command=self.start_simulation)
        self.start_button.pack()

        self.info_label = tk.Label(right, text="Set n and press 'Start Simulation'", font=('Arial', 9))
        self.info_label.pack()

    def get_current_memory_mb(self) -> float:
        if HAS_PSUTIL:
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            return mem_info.rss / (1024 * 1024)
        elif HAS_RESOURCE:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            if sys.platform == 'darwin':
                return usage.ru_maxrss / (1024 * 1024)
            else:
                return usage.ru_maxrss / 1024
        else:
            return -1.0

    def get_cpu_percent(self) -> float:
        """Get current CPU utilization percentage"""
        if HAS_PSUTIL:
            process = psutil.Process(os.getpid())
            return process.cpu_percent(interval=0.1)
        return 0.0

    def monitor_cpu_usage(self):
        """Monitor CPU usage in background"""
        while self.monitoring_cpu:
            cpu = self.get_cpu_percent()
            if self.fcfs_running:
                self.cpu_samples_fcfs.append(cpu)
            if self.look_running:
                self.cpu_samples_look.append(cpu)
            time.sleep(0.1)

    def start_simulation(self):
        if self.generating:
            return
        
        # Read n from input field
        try:
            n_value = int(self.n_input.get())
            if n_value <= 0:
                self.info_label.config(text="Error: n must be positive!", fg='red')
                return
            self.max_requests = n_value
            self.config_label.config(text=f"Current: {self.max_requests}")
        except ValueError:
            self.info_label.config(text="Error: Invalid number!", fg='red')
            return
        
        self.start_button.config(state=tk.DISABLED, text="Running...")
        self.info_label.config(text=f"Generating {self.max_requests} requests (0.4s intervals)...", fg='black')
        self.generated = 0
        self.request_pairs = []
        self.requests_numeric = []
        self.fcfs_states = []
        self.look_states = []
        self.next_request_id = 1
        
        # Reset FCFS
        self.fcfs_floor = 1
        self.fcfs_index = 0
        self.fcfs_phase = "to_start"
        self.fcfs_distance = 0
        self.fcfs_steps = 0
        self.fcfs_wait_times = []
        self.total_pickups_fcfs = 0
        self.fcfs_operations = 0
        
        # Reset LOOK
        self.look_floor = 1
        self.look_direction = 0
        self.look_distance = 0
        self.look_steps = 0
        self.look_wait_times = []
        self.total_pickups_look = 0
        self.look_operations = 0
        
        # Reset CPU tracking
        self.cpu_samples_fcfs = []
        self.cpu_samples_look = []
        
        # Reset visualization
        y_fcfs = self.floor_y[self.fcfs_floor]
        self.canvas.coords(self.elev_fcfs, 80, y_fcfs - 15, 120, y_fcfs + 15)
        y_look = self.floor_y[self.look_floor]
        self.canvas.coords(self.elev_look, 160, y_look - 15, 200, y_look + 15)
        
        # Start CPU monitoring
        self.monitoring_cpu = True
        cpu_thread = threading.Thread(target=self.monitor_cpu_usage, daemon=True)
        cpu_thread.start()
        
        # Start algorithms immediately
        self.generating = True
        self.fcfs_running = True
        self.look_running = True
        self.fcfs_start_time = time.time()
        self.look_start_time = time.time()
        
        # Start generation (every 0.4s)
        self.schedule_generation()
        
        # Start processing (every 0.2s for floor movement)
        self.schedule_processing()

    def schedule_generation(self):
        """Generate new request every 0.4 seconds"""
        if self.generated < self.max_requests:
            floors = ['A', 'B', 'C', 'D']
            s = random.choice(floors)
            d = random.choice(floors)
            while d == s:
                d = random.choice(floors)
            current_time = time.time()
            
            self.request_pairs.append((s, d))
            self.requests_numeric.append(Request(FLOOR_MAP[s], FLOOR_MAP[d], gen_time=current_time, id=self.next_request_id)) 
            self.fcfs_states.append('pending')
            self.look_states.append('pending')
            self.generated += 1
            self.next_request_id += 1
            
            self.update_lists_and_stats()
            
            # Schedule next generation
            self.master.after(self.generation_interval, self.schedule_generation)
        else:
            # All requests generated
            if self.generating:
                self.generating = False
                self.info_label.config(text="All requests generated. Completing simulation...")

    def schedule_processing(self):
        """Process both algorithms every 0.2 seconds (one floor move per step)"""
        # Process FCFS - move one floor
        if self.fcfs_running:
            self.step_fcfs_once()
        
        # Process LOOK - move one floor
        if self.look_running:
            self.step_look_once()
        
        # Update display
        self.update_lists_and_stats()
        
        # Continue if either algorithm is still running
        if self.fcfs_running or self.look_running:
            self.master.after(self.floor_move_interval, self.schedule_processing)
        else:
            # Both complete
            self.monitoring_cpu = False
            self.start_button.config(text="Start Simulation", state=tk.NORMAL)
            self.info_label.config(text="✓ Simulation complete!")
            self.update_lists_and_stats()

    def step_fcfs_once(self):
        """Move FCFS elevator by ONE floor (or handle pickup/dropoff)"""
        if self.fcfs_index >= len(self.requests_numeric):
            if not self.generating:
                self.fcfs_running = False
                self.fcfs_time = time.time() - self.fcfs_start_time
            return
        
        self.fcfs_operations += 1
        r = self.requests_numeric[self.fcfs_index]
        
        if self.fcfs_phase == "to_start":
            # Moving to pickup location
            if self.fcfs_floor < r.start:
                self.fcfs_floor += 1  # Move up one floor
                self.fcfs_distance += 1
            elif self.fcfs_floor > r.start:
                self.fcfs_floor -= 1  # Move down one floor
                self.fcfs_distance += 1
            else:
                # Arrived at pickup location
                wait_time = time.time() - r.gen_time
                self.fcfs_wait_times.append(wait_time)
                self.total_pickups_fcfs += 1
                self.fcfs_states[self.fcfs_index] = 'active'
                self.fcfs_phase = "to_dest"
        else:
            # Moving to destination
            if self.fcfs_floor < r.dest:
                self.fcfs_floor += 1  # Move up one floor
                self.fcfs_distance += 1
            elif self.fcfs_floor > r.dest:
                self.fcfs_floor -= 1  # Move down one floor
                self.fcfs_distance += 1
            else:
                # Arrived at destination
                self.fcfs_states[self.fcfs_index] = 'completed'
                self.fcfs_index += 1
                self.fcfs_phase = "to_start"
        
        # Update visualization
        y = self.floor_y[self.fcfs_floor]
        self.canvas.coords(self.elev_fcfs, 80, y-15, 120, y+15)
        self.fcfs_steps += 1

    def step_look_once(self):
        """Move LOOK elevator by ONE floor (or handle pickup/dropoff)"""
        self.look_operations += 1
        
        # Check for pickups and dropoffs at current floor
        for i, r in enumerate(self.requests_numeric):
            if self.look_states[i] == 'pending' and r.start == self.look_floor:
                wait_time = time.time() - r.gen_time
                self.look_wait_times.append(wait_time)
                self.total_pickups_look += 1
                self.look_states[i] = 'active'
            elif self.look_states[i] == 'active' and r.dest == self.look_floor:
                self.look_states[i] = 'completed'

        # Check if there are outstanding requests
        outstanding = False
        for state in self.look_states:
            if state in ('pending', 'active'):
                outstanding = True
                break
        
        if not outstanding:
            if not self.generating:
                self.look_running = False
                self.look_time = time.time() - self.look_start_time
            return
        
        # Determine direction based on outstanding requests
        up = down = False
        for i, r in enumerate(self.requests_numeric):
            state = self.look_states[i]
            target = None
            if state == 'pending':
                target = r.start
            elif state == 'active':
                target = r.dest
            if target is None:
                continue
            if target > self.look_floor:
                up = True
            elif target < self.look_floor:
                down = True
        
        # Set initial direction if not set
        if self.look_direction == 0:
            if up:
                self.look_direction = 1
            elif down:
                self.look_direction = -1
        else:
            # Change direction if needed
            if self.look_direction == 1 and not up and down:
                self.look_direction = -1
            elif self.look_direction == -1 and not down and up:
                self.look_direction = 1
        
        # Move one floor in current direction
        new_floor = self.look_floor + self.look_direction
        
        # Handle boundaries
        if new_floor < 1:
            new_floor = 1
            if down:
                self.look_direction = 0  # Stop to reassess
        elif new_floor > 4:
            new_floor = 4
            if up:
                self.look_direction = 0  # Stop to reassess
        
        # Only move if we have a direction and the floor is valid
        if new_floor != self.look_floor and self.look_direction != 0:
            self.look_distance += 1
            self.look_floor = new_floor
            y = self.floor_y[self.look_floor]
            self.canvas.coords(self.elev_look, 160, y-15, 200, y+15)
        
        self.look_steps += 1

    def update_lists_and_stats(self):
        self.all_requests_list.delete(0, tk.END)
        completed_fcfs = 0
        completed_look = 0
        for i, (a, b) in enumerate(self.request_pairs):
            st_fcfs = self.fcfs_states[i]
            st_look = self.look_states[i]
            map_state = lambda s: 'P' if s == 'pending' else 'A' if s == 'active' else 'C'
            fcfs_label = map_state(st_fcfs)
            look_label = map_state(st_look)
            if st_fcfs == 'completed': completed_fcfs += 1
            if st_look == 'completed': completed_look += 1
            text = f"({i+1}) {a} -> {b} | FCFS: {fcfs_label} | LOOK: {look_label}"
            self.all_requests_list.insert(tk.END, text)
        
        # Auto-scroll to bottom
        self.all_requests_list.see(tk.END)
        
        self.update_stats(completed_fcfs, completed_look)

    def get_net_memory_usage(self) -> float:
        current_mb = self.get_current_memory_mb()
        if not HAS_RESOURCE and not HAS_PSUTIL:
            return -1.0
        return max(0.0, current_mb - self.baseline_memory_mb)

    def update_stats(self, completed_fcfs=None, completed_look=None):
        if completed_fcfs is None:
            completed_fcfs = self.fcfs_states.count('completed')
        if completed_look is None:
            completed_look = self.look_states.count('completed')

        # Calculate times
        if self.fcfs_running:
            total_time_fcfs = time.time() - self.fcfs_start_time
        else:
            total_time_fcfs = self.fcfs_time
            
        if self.look_running:
            total_time_look = time.time() - self.look_start_time
        else:
            total_time_look = self.look_time
            
        time_ms_fcfs = total_time_fcfs * 1000.0
        time_ms_look = total_time_look * 1000.0
        
        avg_wait_fcfs = sum(self.fcfs_wait_times) / self.total_pickups_fcfs if self.total_pickups_fcfs > 0 else 0.0
        avg_wait_look = sum(self.look_wait_times) / self.total_pickups_look if self.total_pickups_look > 0 else 0.0

        # Throughput: operations per second
        throughput_fcfs = self.fcfs_operations / total_time_fcfs if total_time_fcfs > 0 else 0.0
        throughput_look = self.look_operations / total_time_look if total_time_look > 0 else 0.0

        # CPU Utilization
        avg_cpu_fcfs = sum(self.cpu_samples_fcfs) / len(self.cpu_samples_fcfs) if self.cpu_samples_fcfs else 0.0
        avg_cpu_look = sum(self.cpu_samples_look) / len(self.cpu_samples_look) if self.cpu_samples_look else 0.0

        # Update labels
        self.comp_time_ms_fcfs.config(text=f"{time_ms_fcfs:.0f} ms")
        self.comp_time_ms_look.config(text=f"{time_ms_look:.0f} ms")
        self.comp_steps_fcfs.config(text=str(self.fcfs_steps))
        self.comp_steps_look.config(text=str(self.look_steps))
        self.comp_dist_fcfs.config(text=str(self.fcfs_distance))
        self.comp_dist_look.config(text=str(self.look_distance))
        self.comp_throughput_fcfs.config(text=f"{throughput_fcfs:.2f}")
        self.comp_throughput_look.config(text=f"{throughput_look:.2f}")
        self.comp_wait_fcfs.config(text=f"{avg_wait_fcfs:.2f}s")
        self.comp_wait_look.config(text=f"{avg_wait_look:.2f}s")
        self.comp_cpu_fcfs.config(text=f"{avg_cpu_fcfs:.2f}%")
        self.comp_cpu_look.config(text=f"{avg_cpu_look:.2f}%")

        if not self.fcfs_running and not self.look_running:
            memory_mb = self.get_net_memory_usage()
            if memory_mb < 0:
                self.comp_memory.config(text="Install 'psutil'")
            else:
                self.comp_memory.config(text=f"{memory_mb:.2f} MB")
        else:
            self.comp_memory.config(text="Running...")

        self.comp_completed_fcfs.config(text=f"{completed_fcfs} / {self.generated}")
        self.comp_completed_look.config(text=f"{completed_look} / {self.generated}")

def main(n: Optional[int] = None):
    """
    Main function to run the elevator simulator.
    
    Args:
        n: Optional number of requests to generate. Defaults to 25 if not specified.
    """
    root = tk.Tk()
    root.tk.call('lappend', 'auto_path', '.')
    root.tk.call('font', 'configure', 'TkDefaultFont', '-family', 'Arial', '-size', 10)
    app = ElevatorSimulatorBoth(root, max_requests=n)
    root.mainloop()

if __name__ == "__main__":
    # Check if command line argument is provided
    if len(sys.argv) > 1:
        try:
            n_requests = int(sys.argv[1])
            main(n=n_requests)
        except ValueError:
            print("Error: Please provide a valid integer for the number of requests.")
            print("Usage: python DS_Elevator_Final.py [n]")
            print("Example: python DS_Elevator_Final.py 50")
            sys.exit(1)
    else:
        # Run with default value (25)
        main()
