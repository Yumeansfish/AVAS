import os
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

from core.monitor import MonitorCore


class MonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Monitoring App")
        self.root.geometry("500x350")
        
        # Track the survey generator process to prevent multiple instances
        self.survey_process = None

        # "Configure Survey" button: opens survey_gui.py
        self.survey_button = tk.Button(
            root, text="Configure Survey", command=self.open_survey_gui
        )
        self.survey_button.pack(pady=5)
        
        # Directory selection
        tk.Label(root, text="Select a directory to monitor:", font=("Arial", 12)).pack(pady=10)
        self.path_var = tk.StringVar(value=os.path.expanduser("~/Desktop/video"))
        tk.Entry(root, textvariable=self.path_var, width=40).pack()
        tk.Button(root, text="Browse", command=self.select_folder).pack(pady=5)

        # Start & Stop monitoring buttons
        self.start_button = tk.Button(root, text="Start Monitoring", command=self.start_monitoring)
        self.start_button.pack(pady=10)
        self.stop_button = tk.Button(root, text="Stop Monitoring", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        # Output label (displays current monitoring status)
        self.output_label = tk.Label(root, text="Waiting...", fg="blue", font=("Arial", 10))
        self.output_label.pack(pady=10)

        # MonitorCore object (handles background file detection and page generation)
        self.monitor = MonitorCore()

    def open_survey_gui(self):
        """Opens survey_gui.py for survey configuration (single instance)."""
        if self.survey_process is not None and self.survey_process.poll() is None:
            messagebox.showinfo("Info", "The survey generator is already running.")
            return

        script_path = os.path.join(os.path.dirname(__file__), "survey_gui.py")
        try:
            self.survey_process = subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open survey_gui.py: {e}")

    def select_folder(self):
        """Let the user choose a directory to monitor."""
        folder = filedialog.askdirectory()
        if folder:
            self.path_var.set(folder)

    def start_monitoring(self):
        """Starts monitoring the selected directory."""
        watch_dir = self.path_var.get()
        if not os.path.exists(watch_dir):
            messagebox.showerror("Error", "The selected folder does not exist!")
            return

        self.output_label.config(text=f"Monitoring: {watch_dir}")
        self.monitor.start(watch_dir, self.update_output)
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

    def stop_monitoring(self):
        """Stops monitoring."""
        self.monitor.stop()
        self.output_label.config(text="Monitoring stopped")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def update_output(self, video_name, page_url=None):
        """Update the GUI when a video has been processed."""
        text = f"Processed: {video_name}"
        if page_url:
            text += f"\nLink: {page_url}"
        self.output_label.config(text=text)

if __name__ == "__main__":
    root = tk.Tk()
    app = MonitorApp(root)
    root.mainloop()







