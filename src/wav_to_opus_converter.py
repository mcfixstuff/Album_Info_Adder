import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
class WavToOpusConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("WAV to OPUS Converter")
        self.create_widgets()
    
def create_widgets(self):
        # File selection
        self.file_label = tk.Label(self.root, text="Select WAV files:")
        self.file_label.pack(pady=5)
        
        self.file_entry = tk.Entry(self.root, width=50)
        self.file_entry.pack(pady=5)
        
        self.browse_button = tk.Button(
            self.root, text="Browse", command=self.select_files
        )
        self.browse_button.pack(pady=5)

        # Settings
        settings_frame = tk.Frame(self.root)
        settings_frame.pack(pady=10)

        # Bitrate dropdown
        tk.Label(settings_frame, text="Bitrate:").grid(row=0, column=0, padx=5)
        self.bitrate_var = tk.StringVar(value="128k")
        self.bitrate_menu = ttk.Combobox(
            settings_frame, 
            textvariable=self.bitrate_var,
            values=["64k", "96k", "128k", "160k", "192k"]
        )
        self.bitrate_menu.grid(row=0, column=1, padx=5)

        # Sample rate dropdown
        tk.Label(settings_frame, text="Sample Rate:").grid(row=1, column=0, padx=5)
        self.sample_rate_var = tk.StringVar(value="48000")
        self.sample_rate_menu = ttk.Combobox(
            settings_frame, 
            textvariable=self.sample_rate_var,
            values=["44100", "48000", "96000"]
        )
        self.sample_rate_menu.grid(row=1, column=1, padx=5)

        # Convert button
        self.convert_button = tk.Button(
            self.root, text="Convert to OPUS", command=self.convert_files
        )
        self.convert_button.pack(pady=20)
    
def select_files(self):
        file_paths = filedialog.askopenfilenames(
            filetypes=[("WAV files", "*.wav")]
        )
        if file_paths:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, ', '.join(file_paths))
    
def convert_files(self):
        input_paths = self.file_entry.get().split(', ') if self.file_entry.get() else []
        
        # Validate input
        if not input_paths:
            messagebox.showerror("Error", "Please select at least one WAV file")
            return
        
        try:
            # Get settings
            bitrate = self.bitrate_var.get()
            sample_rate = self.sample_rate_var.get()
            
            for input_path in input_paths:
                # Validate file exists
                if not os.path.exists(input_path):
                    messagebox.showerror("Error", f"File not found: {input_path}")
                    continue
                
                # Generate output path in the same directory as the input file
                base_name = os.path.splitext(os.path.basename(input_path))[0]
                output_dir = os.path.dirname(input_path)
                output_path = os.path.join(output_dir, f"{base_name}.opus")
                
                # Run FFmpeg command
                subprocess.run([
                    "ffmpeg",
                    "-i", input_path,
                    "-b:a", bitrate,
                    "-ar", sample_rate,
                    output_path
                ], check=True)
                
            messagebox.showinfo("Success", f"Converted {len(input_paths)} files to their respective directories")
        except Exception as e:
            messagebox.showerror("Error", str(e))
if __name__ == "__main__":
    root = tk.Tk()
    app = WavToOpusConverter(root)
    root.mainloop()