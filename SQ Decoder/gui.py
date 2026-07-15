import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import numpy as np
import audio
import decoder


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Quadraphonic Decoder")

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.decoder_type = tk.StringVar(value="SQ")

        self.create_widgets()

    def create_widgets(self):
        open_wav_button = ttk.Button(
            self.root,
            text="Open WAV",
            command=self.open_wav
        )
        open_wav_button.grid(row=0, column=0, padx=10, pady=5)

        input_path_label = ttk.Label(
            self.root,
            textvariable=self.input_path
        )
        input_path_label.grid(row=0, column=1, padx=10, pady=5)

        decoder_label = ttk.Label(
            self.root,
            text="Decoder Type:"
        )
        decoder_label.grid(row=1, column=0, padx=10, pady=5)

        decoder_choices = [
            "SQ",
            "QS",
            "EV-4"
        ]

        self.decoder_menu = ttk.Combobox(
            self.root,
            textvariable=self.decoder_type,
            values=decoder_choices,
            state="readonly"
        )
        self.decoder_menu.grid(row=1, column=1, padx=10, pady=5)

        select_output_button = ttk.Button(
            self.root,
            text="Select Output",
            command=self.select_output
        )
        select_output_button.grid(row=2, column=0, padx=10, pady=5)

        output_path_label = ttk.Label(
            self.root,
            textvariable=self.output_path
        )
        output_path_label.grid(row=2, column=1, padx=10, pady=5)

        decode_button = ttk.Button(
            self.root,
            text="Decode",
            command=self.decode_audio
        )
        decode_button.grid(row=3, column=0, padx=10, pady=5)

        self.progress_bar = ttk.Progressbar(
            self.root,
            orient="horizontal",
            length=300,
            mode="determinate"
        )
        self.progress_bar.grid(row=3, column=1, padx=10, pady=5)

        self.status_label = ttk.Label(
            self.root,
            text=""
        )
        self.status_label.grid(
            row=4,
            column=0,
            columnspan=2,
            padx=10,
            pady=5
        )

    def open_wav(self):
        filepath = filedialog.askopenfilename(
            filetypes=[
                ("WAV files", "*.wav")
            ]
        )

        if filepath:
            self.input_path.set(filepath)

    def select_output(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".flac",
            filetypes=[
                ("FLAC files", "*.flac")
            ]
        )

        if filepath:
            self.output_path.set(filepath)

    def decode_audio(self):
        input_filepath = self.input_path.get()
        output_filepath = self.output_path.get()

        if not input_filepath or not output_filepath:
            messagebox.showerror(
                "Error",
                "Both input and output files must be selected."
            )
            return

        thread = threading.Thread(
            target=self.decode_in_thread,
            args=(
                input_filepath,
                output_filepath
            ),
            daemon=True
        )

        thread.start()

    def decode_in_thread(
        self,
        input_filepath,
        output_filepath
    ):
        try:
            self.status_label.config(
                text="Loading WAV..."
            )

            stereo_data, samplerate = audio.load_wav(
                input_filepath
            )

            self.status_label.config(
                text="Decoding..."
            )

            self.progress_bar["value"] = 50

            selected_decoder = self.decoder_type.get()

            if selected_decoder == "SQ":
                decoded_data = decoder.sq_decoder(
                    stereo_data
                )

            elif selected_decoder == "QS":
                decoded_data = decoder.qs_decoder(
                    stereo_data
                )

            elif selected_decoder == "EV-4":
                decoded_data = decoder.ev4_decoder(
                    stereo_data
                )

            else:
                raise ValueError(
                    "Invalid decoder type selected."
                )

            # DEBUG OUTPUT
            print("--------------------------------")
            print("Decoder:", selected_decoder)
            print("Decoded shape:", decoded_data.shape)

            print(
                "FL:",
                np.max(np.abs(decoded_data[:, 0]))
            )

            print(
                "FR:",
                np.max(np.abs(decoded_data[:, 1]))
            )

            print(
                "RL:",
                np.max(np.abs(decoded_data[:, 2]))
            )

            print(
                "RR:",
                np.max(np.abs(decoded_data[:, 3]))
            )

            print("--------------------------------")

            self.status_label.config(
                text="Normalizing..."
            )

            normalized_data = audio.normalize(
                decoded_data
            )

            self.status_label.config(
                text="Creating 5.1 layout..."
            )

            #
            # Create standard 5.1 channel layout:
            #
            # Channel 0 = Front Left
            # Channel 1 = Front Right
            # Channel 2 = Center (silent)
            # Channel 3 = LFE (silent)
            # Channel 4 = Surround Left
            # Channel 5 = Surround Right
            #

            export_data = np.zeros(
                (
                    normalized_data.shape[0],
                    6
                ),
                dtype=np.float32
            )

            export_data[:, 0] = normalized_data[:, 0]
            export_data[:, 1] = normalized_data[:, 1]

            # Center and LFE intentionally silent

            export_data[:, 4] = normalized_data[:, 2]
            export_data[:, 5] = normalized_data[:, 3]

            print("Export channels:")
            print(
                "FL:",
                np.max(np.abs(export_data[:, 0]))
            )
            print(
                "FR:",
                np.max(np.abs(export_data[:, 1]))
            )
            print(
                "C:",
                np.max(np.abs(export_data[:, 2]))
            )
            print(
                "LFE:",
                np.max(np.abs(export_data[:, 3]))
            )
            print(
                "SL:",
                np.max(np.abs(export_data[:, 4]))
            )
            print(
                "SR:",
                np.max(np.abs(export_data[:, 5]))
            )

            self.status_label.config(
                text="Exporting FLAC..."
            )

            self.progress_bar["value"] = 100

            audio.export_flac(
                output_filepath,
                export_data,
                samplerate
            )

            self.status_label.config(
                text="Done!"
            )

            messagebox.showinfo(
                "Complete",
                "5.1 FLAC export completed."
            )

        except Exception as e:
            messagebox.showerror(
                "Error",
                str(e)
            )

        finally:
            self.progress_bar["value"] = 0


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()