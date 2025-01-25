import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
from typing import List, Dict
import time

class Page:
    def __init__(self, value: int):
        self.value = value
        self.reference_bit = 0
        self.counter = 0

class ClockAlgorithmGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Clock Page Replacement Algorithm Visualization")
        
        self.frames = [None] * 3
        self.pointer = 0
        self.page_faults = 0
        self.page_hits = 0
        self.access_count = 0
        self.q_test_results = {}
        self.optimal_q = None
        
        self.request_sequence = []
        self.current_request_idx = 0
        self.is_running = False
        self.fault_rates = []
        
        self.setup_gui()
        self.setup_plot()
        
    def setup_gui(self):
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky="nsew")
        
        input_frame = ttk.LabelFrame(main_container, text="Input Parameters", padding="10")
        input_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        ttk.Label(input_frame, text="Request Sequence:").grid(row=0, column=0, padx=5)
        self.sequence_var = tk.StringVar(value="1,3,5,3,7,1,9,2,5,8,3,2,4")
        sequence_entry = ttk.Entry(input_frame, textvariable=self.sequence_var, width=40)
        sequence_entry.grid(row=0, column=1, padx=5)
        
        ttk.Button(input_frame, text="Generate Random", 
                  command=self.generate_random_sequence).grid(row=0, column=2, padx=5)
        
        ttk.Label(input_frame, text="Time Cutoff (Q):").grid(row=1, column=0, padx=5)
        self.q_value = tk.StringVar(value="2")
        q_entry = ttk.Entry(input_frame, textvariable=self.q_value, width=5)
        q_entry.grid(row=1, column=1, sticky="w", padx=5)
        
        ttk.Label(input_frame, text="Animation Speed (ms):").grid(row=2, column=0, padx=5)
        self.speed_var = tk.StringVar(value="1000")
        speed_entry = ttk.Entry(input_frame, textvariable=self.speed_var, width=5)
        speed_entry.grid(row=2, column=1, sticky="w", padx=5)
        
        control_frame = ttk.Frame(input_frame)
        control_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        self.start_button = ttk.Button(control_frame, text="Start", command=self.toggle_simulation)
        self.start_button.grid(row=0, column=0, padx=5)
        
        ttk.Button(control_frame, text="Reset", 
                  command=self.reset_simulation).grid(row=0, column=1, padx=5)
        
        ttk.Button(control_frame, text="Find Optimal Q", 
                  command=self.find_optimal_q).grid(row=0, column=2, padx=5)
        
        frames_frame = ttk.LabelFrame(main_container, text="Memory Frames", padding="10")
        frames_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        self.frame_labels = []
        for i in range(3):
            frame = ttk.Frame(frames_frame, relief="solid", padding="10")
            frame.grid(row=0, column=i, padx=5)
            value_label = ttk.Label(frame, text="-")
            value_label.grid(row=0, column=0)
            ref_label = ttk.Label(frame, text="Ref: 0")
            ref_label.grid(row=1, column=0)
            counter_label = ttk.Label(frame, text="Counter: 0")
            counter_label.grid(row=2, column=0)
            self.frame_labels.append((value_label, ref_label, counter_label))
        
        stats_frame = ttk.LabelFrame(main_container, text="Statistics", padding="10")
        stats_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        
        self.stats_label = ttk.Label(stats_frame)
        self.stats_label.grid(row=0, column=0)
        
        self.plot_frame = ttk.Frame(main_container)
        self.plot_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        
    def setup_plot(self):
        self.figure = Figure(figsize=(8, 4))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.ax.set_title("Page Fault Rate Over Time")
        self.ax.set_xlabel("Access Count")
        self.ax.set_ylabel("Fault Rate (%)")
        
    def generate_random_sequence(self):
        sequence = [random.randint(1, 10) for _ in range(15)]
        self.sequence_var.set(",".join(map(str, sequence)))
        
    def update_plot(self):
        self.ax.clear()
        self.ax.plot(range(len(self.fault_rates)), self.fault_rates, marker='o')
        self.ax.set_title("Page Fault Rate Over Time")
        self.ax.set_xlabel("Access Count")
        self.ax.set_ylabel("Fault Rate (%)")
        self.canvas.draw()
        
    def update_display(self):
        for i, (value_label, ref_label, counter_label) in enumerate(self.frame_labels):
            if self.frames[i] is None:
                value_label.config(text="-")
                ref_label.config(text="Ref: 0")
                counter_label.config(text="Counter: 0")
            else:
                value_label.config(text=str(self.frames[i].value))
                ref_label.config(text=f"Ref: {self.frames[i].reference_bit}")
                counter_label.config(text=f"Counter: {self.frames[i].counter}")
        
        fault_rate = (self.page_faults / (self.access_count or 1)) * 100
        hit_rate = (self.page_hits / (self.access_count or 1)) * 100
        stats_text = (f"Access Count: {self.access_count}\n"
                     f"Page Faults: {self.page_faults}\n"
                     f"Page Hits: {self.page_hits}\n"
                     f"Fault Rate: {fault_rate:.2f}%\n"
                     f"Hit Rate: {hit_rate:.2f}%")
        self.stats_label.config(text=stats_text)
        
        self.fault_rates.append(fault_rate)
        self.update_plot()
        
    def find_page(self, page_value: int) -> int:
        return next((i for i, frame in enumerate(self.frames) 
                    if frame and frame.value == page_value), -1)
        
    def access_page(self):
        try:
            request_sequence = [int(x.strip()) for x in self.sequence_var.get().split(',')]
        except ValueError:
            messagebox.showerror("Error", "Invalid request sequence format")
            self.is_running = False
            self.start_button.config(text="Start")
            return
            
        if self.current_request_idx >= len(request_sequence):
            self.is_running = False
            self.start_button.config(text="Start")
            return
            
        page_value = request_sequence[self.current_request_idx]
        self.access_count += 1
        page_index = self.find_page(page_value)
        
        if page_index != -1:
            self.page_hits += 1
            self.frames[page_index].reference_bit = 1
            self.frames[page_index].counter = int(self.q_value.get())
        else:
            self.page_faults += 1
            self._handle_page_fault(page_value)
            
        self.update_display()
        self.current_request_idx += 1
        
        if self.is_running:
            try:
                speed = int(self.speed_var.get())
            except ValueError:
                speed = 1000
            self.root.after(speed, self.access_page)
            
    def _handle_page_fault(self, page_value: int):
        while True:
            if self.frames[self.pointer] is None:
                self.frames[self.pointer] = Page(page_value)
                self.frames[self.pointer].reference_bit = 1
                self.frames[self.pointer].counter = int(self.q_value.get())
                self.pointer = (self.pointer + 1) % len(self.frames)
                return
                
            if self.frames[self.pointer].counter == 0:
                self.frames[self.pointer] = Page(page_value)
                self.frames[self.pointer].reference_bit = 1
                self.frames[self.pointer].counter = int(self.q_value.get())
                self.pointer = (self.pointer + 1) % len(self.frames)
                return
                
            self.frames[self.pointer].counter -= 1
            self.pointer = (self.pointer + 1) % len(self.frames)
            
    def find_optimal_q(self):
        self.q_test_results.clear()
    
        try:
            request_sequence = [int(x.strip()) for x in self.sequence_var.get().split(',')]
        
            for test_q in range(1, 6):
                frames = [None] * 3
                pointer = 0
                page_faults = 0
                access_count = 0
                total_search_time = 0  # New metric for search overhead
            
                for page_value in request_sequence:
                    access_count += 1
                    search_steps = 0  # Track steps needed to find/place a page
                
                    # Find existing page
                    page_index = next((i for i, frame in enumerate(frames) 
                                    if frame and frame.value == page_value), -1)
                
                    if page_index != -1:
                        # Page hit - minimal cost
                        frames[page_index].reference_bit = 1
                        frames[page_index].counter = test_q // 2  # Partial reset
                        search_steps += 1
                    else:
                        # Page fault - need to find replacement
                        page_faults += 1
                        replacement_found = False
                        original_pointer = pointer
                    
                        while not replacement_found:
                            search_steps += 1
                        
                            if frames[pointer] is None:
                                frames[pointer] = Page(page_value)
                                frames[pointer].reference_bit = 1
                                frames[pointer].counter = test_q
                                replacement_found = True
                            elif frames[pointer].counter == 0:
                                frames[pointer] = Page(page_value)
                                frames[pointer].reference_bit = 1
                                frames[pointer].counter = test_q
                                replacement_found = True
                            else:
                                frames[pointer].counter -= 1
                                pointer = (pointer + 1) % len(frames)
                            
                                # Detect full cycle without replacement
                                if pointer == original_pointer and not replacement_found:
                                    frames[pointer] = Page(page_value)
                                    frames[pointer].reference_bit = 1
                                    frames[pointer].counter = test_q
                                    replacement_found = True
                
                    total_search_time += search_steps
                    pointer = (pointer + 1) % len(frames)
            
                # Calculate metrics with different weights
                fault_rate = (page_faults / access_count) * 100
                avg_search_time = total_search_time / access_count
                overhead_penalty = (test_q / 5) * 10  # Larger Q means more overhead
            
                # Composite score balancing fault rate, search time, and Q overhead
                composite_score = (
                    (fault_rate * 0.6) +          # Weight fault rate most heavily
                    (avg_search_time * 0.25) +     # Consider search efficiency
                    (overhead_penalty * 0.15)      # Penalize higher Q values
                )
            
                self.q_test_results[test_q] = round(composite_score, 2)
        
            # Find optimal q
            self.optimal_q = min(self.q_test_results.items(), key=lambda x: x[1])[0]
        
            # Display results
            results_window = tk.Toplevel(self.root)
            results_window.title("Q Value Analysis Results")
        
            ttk.Label(results_window, text="Q Value Analysis Results", 
                    font=('TkDefaultFont', 11, 'bold')).pack(padx=10, pady=5)
        
            for q, score in sorted(self.q_test_results.items()):
                frame = ttk.Frame(results_window)
                frame.pack(fill='x', padx=10, pady=2)
                ttk.Label(frame, text=f"Q = {q}:", width=10).pack(side='left')
                ttk.Label(frame, text=f"Performance Score = {score:.2f}").pack(side='left')
        
            ttk.Label(results_window, 
                    text=f"\nRecommended Q value: {self.optimal_q}",
                    font=('TkDefaultFont', 10, 'bold')).pack(padx=10, pady=5)
        
            explanation = (
                f"The recommended Q value of {self.optimal_q} optimizes the balance between:\n\n"
                f"• Page fault frequency\n"
                f"• Memory access efficiency\n"
                f"• Algorithm overhead\n\n"
                f"Lower Q values allow faster page replacement but may increase faults, "
                f"while higher Q values reduce faults but increase memory management overhead."
            )
            ttk.Label(results_window, text=explanation, wraplength=300).pack(padx=10, pady=5)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid request sequence format")
            return
            
    def toggle_simulation(self):
        self.is_running = not self.is_running
        self.start_button.config(text="Pause" if self.is_running else "Start")
        if self.is_running:
            self.access_page()
            
    def reset_simulation(self):
        self.frames = [None] * 3
        self.pointer = 0
        self.page_faults = 0
        self.page_hits = 0
        self.access_count = 0
        self.current_request_idx = 0
        self.is_running = False
        self.fault_rates = []
        self.start_button.config(text="Start")
        self.update_display()

def main():
    root = tk.Tk()
    app = ClockAlgorithmGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()