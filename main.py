"""
main.py

Entry point for Vinyl Metadata Helper
"""

import tkinter as tk
from gui import VinylApp


def main():
    root = tk.Tk()
    root.title("Vinyl Metadata Helper")

    app = VinylApp(root)

    root.mainloop()


if __name__ == "__main__":
    main()