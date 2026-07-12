import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
MULTIPLE_VALUES = "(Multiple Values)"
try:
    from mutagen import File as MutagenFile
except ModuleNotFoundError:  # pragma: no cover - exercised when dependency is missing
    MutagenFile = None


def _require_mutagen():
    if MutagenFile is None:
        python_path = sys.executable or os.sys.executable
        raise ModuleNotFoundError(
            "mutagen is required to edit audio metadata. "
            f"This app is running with: {python_path}. "
            "Install it into that interpreter with: python -m pip install mutagen"
        )
    return MutagenFile


def get_audio_files(folder):
    files = []
    for path in Path(folder).iterdir():
        if not path.is_file():
            continue
        try:
            if MutagenFile(path):
                files.append(path)
        except Exception:
            continue

    return sorted(files, key=lambda path: path.name.lower())


def get_opus_files(folder):
    return get_audio_files(folder)


def build_metadata_payload(tags):
    payload = {}
    for key, value in tags.items():
        if isinstance(value, list) and value:
            payload[key.lower()] = str(value[0])
        elif value is not None:
            payload[key.lower()] = str(value)
    return {
        "title": payload.get("title", ""),
        "artist": payload.get("artist", ""),
        "albumartist": payload.get("albumartist", ""),
        "album": payload.get("album", ""),
        "date": payload.get("date", ""),
        "tracknumber": payload.get("tracknumber", ""),
        "genre": payload.get("genre", ""),
    }


def load_metadata(file_path):
    mutagen_file = _require_mutagen()
    audio = mutagen_file(file_path)
    return build_metadata_payload(audio)


def save_metadata(file_path, values):
    mutagen_file = _require_mutagen()
    audio = mutagen_file(file_path)

    for key, value in values.items():
        tag_name = {
            "title": "TITLE",
            "artist": "ARTIST",
            "albumartist": "ALBUMARTIST",
            "album": "ALBUM",
            "date": "DATE",
            "genre": "GENRE",
            "tracknumber": "TRACKNUMBER",
        }.get(key)

        if tag_name:
            if value:
                audio[tag_name] = [value]
            else:
                audio.pop(tag_name, None)

    audio.save()
    return True


class MetadataEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Opus Metadata Editor")
        self.root.geometry("900x620")

        self.folder_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Choose a folder of .opus files to begin.")
        self.file_list = []
        self.current_files = []
        self.original_display = {}
        self.fields = {}

        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        top = ttk.Frame(main)
        top.pack(fill="x")
        ttk.Button(top, text="Open folder", command=self.open_folder).pack(side="left")
        ttk.Label(top, textvariable=self.folder_var, wraplength=650).pack(side="left", padx=(10, 0))

        splitter = ttk.PanedWindow(main, orient="horizontal")
        splitter.pack(fill="both", expand=True, pady=(10, 0))

        left = ttk.Frame(splitter, padding=6)
        splitter.add(left, weight=1)

        self.file_tree = ttk.Treeview(
            left,
            columns=("name",),
            show="headings",
            height=16,
            selectmode="extended"
        )
        self.file_tree.heading("name", text="Files")
        self.file_tree.column("name", width=220)
        self.file_tree.pack(fill="both", expand=True)
        self.file_tree.bind("<<TreeviewSelect>>", self.on_file_selected)

        right = ttk.Frame(splitter, padding=6)
        splitter.add(right, weight=2)

        form = ttk.LabelFrame(right, text="Metadata")
        form.pack(fill="both", expand=True)

        fields = [
            ("Title", "title"),
            ("Artist", "artist"),
            ("Album Artist", "albumartist"),
            ("Album", "album"),
            ("Date", "date"),
            ("Track Number", "tracknumber"),
            ("Genre", "genre"),
        ]

        for label_text, key in fields:
            row = ttk.Frame(form)
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=label_text, width=14).pack(side="left")
            entry = ttk.Entry(row)
            entry.pack(side="left", fill="x", expand=True)
            self.fields[key] = entry

        buttons = ttk.Frame(right)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="Save", command=self.save_current_file).pack(side="left")

        ttk.Label(main, textvariable=self.status_var, wraplength=850).pack(anchor="w", pady=(10, 0))

    def open_folder(self):
        folder = filedialog.askdirectory(title="Choose folder with .opus files")
        if not folder:
            return

        self.folder_var.set(folder)
        self.file_list = get_audio_files(folder)

        for child in self.file_tree.get_children():
            self.file_tree.delete(child)

        for file_path in self.file_list:
            self.file_tree.insert("", "end", values=(file_path.name,))

        if self.file_list:
            self.file_tree.selection_set(self.file_tree.get_children()[0])
            self.on_file_selected(None)
            self.status_var.set(f"Loaded {len(self.file_list)} file(s) from {folder}")
        else:
            self.status_var.set("No .opus files found in that folder.")

    def on_file_selected(self, _event):
        selection = self.file_tree.selection()
        if not selection:
            return

        folder = Path(self.folder_var.get())

        self.current_files = []
        metadata_list = []

        for item in selection:
            file_name = self.file_tree.item(item, "values")[0]
            path = folder / file_name

            self.current_files.append(path)

            try:
                metadata_list.append(load_metadata(path))
            except Exception as exc:
                messagebox.showerror("Load failed", str(exc))
                return

        self.original_display = {}

        for key, entry in self.fields.items():
            values = [metadata.get(key, "") for metadata in metadata_list]

            unique = set(values)

            if len(unique) == 1:
                display = values[0]
            else:
                non_empty = {v for v in unique if v}

                if len(non_empty) == 0:
                    display = ""
                else:
                    display = MULTIPLE_VALUES

            self.original_display[key] = display

            entry.delete(0, tk.END)
            entry.insert(0, display)
            
    def save_current_file(self):
        if not self.current_files:
            messagebox.showwarning(
                "No file selected",
                "Choose one or more files first."
            )
            return

        updates = {}

        for key, entry in self.fields.items():
            current = entry.get().strip()
            original = self.original_display.get(key, "")

            # User left "(Multiple Values)" untouched.
            # Don't modify that tag on any files.
            if original == MULTIPLE_VALUES and current == MULTIPLE_VALUES:
                continue

            updates[key] = current

        try:
            for file_path in self.current_files:
                metadata = load_metadata(file_path)

                for key, value in updates.items():
                    metadata[key] = value

                save_metadata(file_path, metadata)

        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))
            return

        if len(self.current_files) == 1:
            self.status_var.set(
                f"Saved metadata to {self.current_files[0].name}"
            )
            messagebox.showinfo(
                "Saved",
                f"Saved metadata to {self.current_files[0].name}"
            )
        else:
            self.status_var.set(
                f"Updated metadata for {len(self.current_files)} files."
            )
            messagebox.showinfo(
                "Saved",
                f"Updated metadata for {len(self.current_files)} files."
            )

        # Reload display to refresh "(Multiple Values)" fields
        self.on_file_selected(None)


def main():
    root = tk.Tk()
    app = MetadataEditorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
