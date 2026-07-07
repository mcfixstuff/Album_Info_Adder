import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from parser import parse_discogs
from tagger import preview, rename_files, write_tags


def build_preview_rows(discogs_text, folder, parse_options=None):
    album_data = parse_discogs(discogs_text, **(parse_options or {}))
    rows = preview(folder, album_data)
    return album_data, rows


def needs_review(album_data):
    if not album_data.get("tracks"):
        return True
    if not album_data.get("album") and not album_data.get("album_artist"):
        return True
    if album_data.get("year") in {None, ""}:
        return True
    return False


class VinylApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vinyl Metadata Helper")
        self.root.geometry("760x560")

        self.discogs_text = tk.StringVar()
        self.folder_path = tk.StringVar()
        self.year_var = tk.StringVar()
        self.ignore_commas_var = tk.BooleanVar(value=False)
        self.ignore_parentheses_var = tk.BooleanVar(value=False)
        self.keep_numeric_titles_var = tk.BooleanVar(value=False)
        self.handle_track_codes_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Paste Discogs text and choose a folder to begin.")

        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Discogs text").pack(anchor="w")
        self.text_box = tk.Text(main, height=16, wrap="word")
        self.text_box.pack(fill="both", expand=True, pady=(4, 10))

        controls = ttk.Frame(main)
        controls.pack(fill="x", pady=(0, 10))

        ttk.Button(controls, text="Choose folder", command=self.choose_folder).pack(side="left")
        ttk.Label(controls, textvariable=self.folder_path, wraplength=480).pack(side="left", padx=(10, 0))

        year_row = ttk.Frame(main)
        year_row.pack(fill="x", pady=(0, 8))
        ttk.Label(year_row, text="Year (optional):").pack(side="left")
        ttk.Entry(year_row, textvariable=self.year_var, width=20).pack(side="left", padx=(6, 0))
        ttk.Label(year_row, text="Leave blank to skip adding a year").pack(side="left", padx=(8, 0))

        options_row = ttk.Frame(main)
        options_row.pack(fill="x", pady=(0, 6))
        ttk.Checkbutton(options_row, text="Ignore commas as track separators", variable=self.ignore_commas_var).pack(side="left")
        ttk.Checkbutton(options_row, text="Ignore parentheses as track separators", variable=self.ignore_parentheses_var).pack(side="left", padx=(12, 0))
        ttk.Checkbutton(options_row, text="Keep numeric titles", variable=self.keep_numeric_titles_var).pack(side="left", padx=(12, 0))
        ttk.Checkbutton(options_row, text="Handle A1/B1-style track codes", variable=self.handle_track_codes_var).pack(side="left", padx=(12, 0))

        buttons = ttk.Frame(main)
        buttons.pack(fill="x", pady=(0, 10))
        ttk.Button(buttons, text="Preview", command=self.preview).pack(side="left")
        ttk.Button(buttons, text="Apply tags", command=self.apply_tags).pack(side="left", padx=(8, 0))

        self.tree = ttk.Treeview(main, columns=("track", "file", "title", "artist"), show="headings", height=10)
        self.tree.heading("track", text="Track")
        self.tree.heading("file", text="File")
        self.tree.heading("title", text="Title")
        self.tree.heading("artist", text="Artist")
        self.tree.column("track", width=60, anchor="center")
        self.tree.column("file", width=180)
        self.tree.column("title", width=260)
        self.tree.column("artist", width=220)
        self.tree.pack(fill="both", expand=True)

        ttk.Label(main, textvariable=self.status_var, wraplength=720).pack(anchor="w", pady=(8, 0))

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Choose folder containing .opus files")
        if folder:
            self.folder_path.set(folder)
            self.status_var.set(f"Folder selected: {folder}")

    def get_parse_options(self):
        return {
            "ignore_commas": self.ignore_commas_var.get(),
            "ignore_parentheses": self.ignore_parentheses_var.get(),
            "keep_numeric_titles": self.keep_numeric_titles_var.get(),
            "handle_track_codes": self.handle_track_codes_var.get(),
        }

    def preview(self):
        folder = self.folder_path.get().strip()
        if not folder:
            messagebox.showwarning("Missing folder", "Choose a folder containing .opus files first.")
            return

        discogs_text = self.text_box.get("1.0", "end").strip()
        if not discogs_text:
            messagebox.showwarning("Missing input", "Paste Discogs text into the box first.")
            return

        try:
            album_data, rows = build_preview_rows(discogs_text, folder, self.get_parse_options())
            year_value = self.year_var.get().strip()
            if year_value:
                album_data["year"] = year_value
            elif not album_data.get("year"):
                album_data["year"] = ""
            elif not self.year_var.get().strip():
                self.year_var.set(album_data.get("year", ""))
        except Exception as exc:
            messagebox.showerror("Parse failed", str(exc))
            return

        for row in self.tree.get_children():
            self.tree.delete(row)

        for row in rows:
            self.tree.insert("", "end", values=(row["track"], row["file"], row["title"], row["artist"]))

        self.status_var.set(f"Previewed {len(rows)} tracks from {album_data['album'] or album_data['album_artist']}")

        if needs_review(album_data):
            self.show_review_window(album_data, rows)

    def show_review_window(self, album_data, rows):
        review = tk.Toplevel(self.root)
        review.title("Review Parsed Metadata")
        review.geometry("720x520")

        ttk.Label(review, text="Please review the parsed metadata before applying tags.").pack(anchor="w", padx=12, pady=(10, 6))

        info = ttk.LabelFrame(review, text="Parsed info")
        info.pack(fill="x", padx=12, pady=(0, 8))

        ttk.Label(info, text=f"Album: {album_data.get('album', '')}").pack(anchor="w", padx=8, pady=2)
        ttk.Label(info, text=f"Artist: {album_data.get('album_artist', '')}").pack(anchor="w", padx=8, pady=2)
        ttk.Label(info, text=f"Year: {album_data.get('year', '')}").pack(anchor="w", padx=8, pady=2)
        ttk.Label(info, text=f"Tracks parsed: {len(rows)}").pack(anchor="w", padx=8, pady=2)

        preview_frame = ttk.LabelFrame(review, text="Track preview")
        preview_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        tree = ttk.Treeview(preview_frame, columns=("track", "title", "artist"), show="headings", height=12)
        tree.heading("track", text="Track")
        tree.heading("title", text="Title")
        tree.heading("artist", text="Artist")
        tree.column("track", width=60, anchor="center")
        tree.column("title", width=320)
        tree.column("artist", width=240)
        tree.pack(fill="both", expand=True)

        for row in rows:
            tree.insert("", "end", values=(row["track"], row["title"], row["artist"]))

        buttons = ttk.Frame(review)
        buttons.pack(fill="x", padx=12, pady=(0, 10))
        ttk.Button(buttons, text="Looks correct", command=review.destroy).pack(side="left")
        ttk.Button(buttons, text="Cancel", command=review.destroy).pack(side="left", padx=(8, 0))

    def apply_tags(self):
        folder = self.folder_path.get().strip()
        if not folder:
            messagebox.showwarning("Missing folder", "Choose a folder containing .opus files first.")
            return

        discogs_text = self.text_box.get("1.0", "end").strip()
        if not discogs_text:
            messagebox.showwarning("Missing input", "Paste Discogs text into the box first.")
            return

        try:
            album_data = parse_discogs(discogs_text, **self.get_parse_options())
            year_value = self.year_var.get().strip()
            if year_value:
                album_data["year"] = year_value
            elif not album_data.get("year"):
                album_data["year"] = ""
            elif not self.year_var.get().strip():
                self.year_var.set(album_data.get("year", ""))
            count = write_tags(folder, album_data)
            rename_files(folder, album_data)
        except Exception as exc:
            messagebox.showerror("Tagging failed", str(exc))
            return

        self.status_var.set(f"Updated {count} files successfully.")
        messagebox.showinfo("Done", f"Updated {count} files.")