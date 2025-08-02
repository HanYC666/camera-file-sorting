import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Advanced Metadata GUI")
        self.geometry("1200x700")
        self.configure(bg="white")

        # Load the image for the home page
        self.image_path = "image.png"  # Update this with the path to your uploaded image
        self.image = Image.open(self.image_path)

        # Resize the image if it's too large, maintaining aspect ratio
        max_width, max_height = 400, 400  # Max dimensions for the image
        aspect_ratio = self.image.width / self.image.height
        if self.image.width > max_width or self.image.height > max_height:
            if aspect_ratio > 1:  # Landscape
                new_width = max_width
                new_height = int(max_width / aspect_ratio)
            else:  # Portrait
                new_height = max_height
                new_width = int(max_height * aspect_ratio)
            self.image = self.image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        self.home_image = ImageTk.PhotoImage(self.image)

        # Create sidebar
        self.sidebar = tk.Frame(self, bg="white", width=200)
        self.sidebar.pack(side="left", fill="y")

        # Add buttons to sidebar
        self.buttons = {
            "Home": self.show_home,
            "Configuration Editor": self.show_config_editor,
            "Import": self.show_import,
            "Backup": self.show_backup,
        }

        for idx, (text, command) in enumerate(self.buttons.items()):
            btn = tk.Button(
                self.sidebar,
                text=text,
                command=command,
                bg="white",
                fg="black",
                font=("Arial", 12, "bold"),
                bd=0,
                pady=10,
                anchor="w",
            )
            btn.pack(fill="x", padx=10, pady=5)

        # Add a gear icon at the bottom of the sidebar for "Settings"
        self.settings_icon = tk.Label(self.sidebar, text="⚙", font=("Arial", 16))
        self.settings_icon.pack(side="bottom", pady=20)

        # Main content area
        self.main_frame = tk.Frame(self, bg="white")
        self.main_frame.pack(side="right", fill="both", expand=True)

        # Initialize with Home page
        self.show_home()

    def clear_main_frame(self):
        """Clear the content of the main frame."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_home(self):
        self.clear_main_frame()

        # Add the title at the top of the Home page
        tk.Label(
            self.main_frame,
            text="Home",
            font=("Arial", 24, "bold"),
            bg="white",
        ).pack(pady=(20, 10))  # Padding at the top and between title and image

        # Add the image to the center of the Home page
        image_label = tk.Label(self.main_frame, image=self.home_image, bg="white")
        image_label.pack(pady=20)  # Adjust padding as needed

    def show_config_editor(self):
        self.clear_main_frame()
        tk.Label(
            self.main_frame,
            text="Configuration Editor",
            font=("Arial", 24, "bold"),
            bg="white",
        ).pack(pady=20)

    def show_import(self):
        self.clear_main_frame()
        tk.Label(
            self.main_frame,
            text="Import",
            font=("Arial", 24, "bold"),
            bg="white",
        ).pack(pady=20)

    def show_backup(self):
        self.clear_main_frame()
        tk.Label(
            self.main_frame,
            text="Backup",
            font=("Arial", 24, "bold"),
            bg="white",
        ).pack(pady=20)


if __name__ == "__main__":
    app = App()
    app.mainloop()
