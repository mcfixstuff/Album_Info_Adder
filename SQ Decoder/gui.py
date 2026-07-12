import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import audio
import decoder

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("SQ Decoder")
        
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        
        self.create_widgets()
    
    def create_widgets(self):
        # Open WAV button
        open_wav_button = ttk.Button(self.root, text="Open WAV", command=self.open_wav)
        open_wav_button.grid(row=0, column=0, padx=10, pady=5)
        
        # Input path label
        input_path_label = ttk.Label(self.root, textvariable=self.input_path)
        input_path_label.grid(row=0, column=1, padx=10, pady=5)
        
        # Output filename/location selector
        select_output_button = ttk.Button(self.root, text="Select Output", command=self.select_output)
        select_output_button.grid(row=1, column=0, padx=10, pady=5)
        
        # Output path label
        output_path_label = ttk.Label(self.root, textvariable=self.output_path)
        output_path_label.grid(row=1, column=1, padx=10, pady=5)
        
        # Decode button
        decode_button = ttk.Button(self.root, text="Decode", command=self.decode_audio)
        decode_button.grid(row=2, column=0, padx=10, pady=5)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.grid(row=2, column=1, padx=10, pady=5)
        
        # Status label
        self.status_label = ttk.Label(self.root, text="")
        self.status_label.grid(row=3, column=0, columnspan=2, padx=10, pady=5)
    
    def open_wav(self):
        filepath = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if filepath:
            self.input_path.set(filepath)
    
    def select_output(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".flac", filetypes=[("FLAC files", "*.flac")])
        if filepath:
            self.output_path.set(filepath)
    
    def decode_audio(self):
        input_filepath = self.input_path.get()
        output_filepath = self.output_path.get()
        
        if not input_filepath or not output_filepath:
            messagebox.showerror("Error", "Both input and output files must be selected.")
            return
        
        thread = threading.Thread(target=self.decode_in_thread, args=(input_filepath, output_filepath))
        thread.start()
    
    def decode_in_thread(self, input_filepath, output_filepath):
        try:
            self.status_label.config(text="Loading WAV...")
            stereo_data, samplerate = audio.load_wav(input_filepath)
            
            self.status_label.config(text="Decoding...")
            self.progress_bar["value"] = 50
            decoded_data = decoder.sq_decoder(stereo_data)
            
            self.status_label.config(text="Normalizing...")
            normalized_data = audio.normalize(decoded_data)
            
            self.status_label.config(text="Exporting FLAC...")
            self.progress_bar["value"] = 100
            audio.export_flac(output_filepath, normalized_data, samplerate)
            
            self.status_label.config(text="Done!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.progress_bar["value"] = 0