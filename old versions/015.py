import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import shutil
import threading
import subprocess


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Advanced Metadata GUI")
        self.geometry("1200x700")
        self.configure(bg="white")

        # Load a home image
        try:
            self.home_image = ImageTk.PhotoImage(Image.open("image.png"))  # Replace with the path to your image
        except Exception as e:
            print(f"Error loading image: {e}")
            self.home_image = None

        # Sidebar
        self.sidebar = tk.Frame(self, bg="white", width=200)
        self.sidebar.pack(side="left", fill="y")

        # Add buttons to sidebar
        self.buttons = {
            "Home": self.show_home,
            "Import": self.show_import,
            "Configuration Editor": self.show_config_editor,
        }
        for text, command in self.buttons.items():
            tk.Button(
                self.sidebar,
                text=text,
                command=command,
                bg="white",
                fg="black",
                font=("Arial", 12, "bold"),
                bd=0,
                pady=10,
                anchor="w",
            ).pack(fill="x", padx=10, pady=5)

        # Main content area
        self.main_frame = tk.Frame(self, bg="white")
        self.main_frame.pack(side="right", fill="both", expand=True)

        # Initialize with Home page
        self.source_data = []  # Store metadata (camera model, date, and file paths)
        self.destination_paths = {}  # Store destination paths for groups
        self.size_check_enabled = tk.BooleanVar(value=False)  # Checkbox for size check
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
        if self.home_image:
            image_label = tk.Label(self.main_frame, image=self.home_image, bg="white")
            image_label.pack(pady=20)  # Adjust padding as needed
        else:
            tk.Label(
                self.main_frame,
                text="No image available",
                font=("Arial", 12),
                bg="white",
                fg="grey",
            ).pack(pady=20)

    def show_import(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Import", font=("Arial", 24, "bold"), bg="white").pack(pady=20)

        # Instruction label
        tk.Label(self.main_frame, text="Select the Parent Source Folder:", font=("Arial", 12), bg="white").pack(pady=10)

        # Display selected folder path
        self.folder_path_var = tk.StringVar(value="No folder selected")
        folder_label = tk.Label(
            self.main_frame, textvariable=self.folder_path_var, font=("Arial", 10), bg="white", fg="grey", wraplength=800, anchor="w"
        )
        folder_label.pack(pady=10, padx=20, fill="x")

        # Select folder button
        tk.Button(
            self.main_frame,
            text="Select Folder",
            command=self.select_folder,
            bg="white",
            font=("Arial", 12),
            padx=10,
        ).pack(pady=10)

    def select_folder(self):
        """Open a dialog to select a folder."""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path_var.set(folder)
            # Process the folder in a new thread to avoid blocking the UI
            threading.Thread(target=self.process_metadata, args=(folder,)).start()

    def process_metadata(self, folder):
        """Process metadata from all files in the selected folder."""
        popup = self.show_popup("Reading Metadata...")
        self.source_data = []  # Reset previous data

        for root, _, files in os.walk(folder):
            for file in files:
                if not file.startswith("."):  # Ignore hidden files
                    file_path = os.path.join(root, file)
                    try:
                        # Use exiftool to extract camera model and date
                        exiftool_output = subprocess.run(
                            ["exiftool.exe", "-Model", "-DateTimeOriginal", file_path],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        output_lines = exiftool_output.stdout.split("\n")
                        camera_model = None
                        date_time = None
                        for line in output_lines:
                            if "Model" in line:
                                camera_model = line.split(":")[1].strip()
                            if "Date/Time Original" in line:
                                date_time = line.split(":")[1].strip()

                        if camera_model and date_time:
                            date_only = date_time.split()[0].replace(":", "/")  # Extract date only in DD/MM/YYYY format
                            self.source_data.append({
                                "camera": camera_model,
                                "date": date_only,
                                "path": file_path
                            })

                    except Exception as e:
                        print(f"Error reading metadata from {file}: {e}")

        popup.destroy()
        self.show_config_editor()

    def show_config_editor(self):
        self.clear_main_frame()
        tk.Label(self.main_frame, text="Configuration Editor", font=("Arial", 24, "bold"), bg="white").pack(pady=20)

        # Create the configuration editor table
        content_frame = tk.Frame(self.main_frame, bg="white")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Headers
        tk.Label(content_frame, text="Source Node", font=("Arial", 12, "bold"), bg="white").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        tk.Label(content_frame, text="Destination Node", font=("Arial", 12, "bold"), bg="white").grid(row=0, column=1, padx=10, pady=5, sticky="w")

        # Populate the table
        self.destination_paths = {}
        grouped_data = {}
        for item in self.source_data:
            group_key = f"{item['camera']} - {item['date']}"
            if group_key not in grouped_data:
                grouped_data[group_key] = []
            grouped_data[group_key].append(item)

        for i, (group_key, items) in enumerate(grouped_data.items(), start=1):
            # Source Node
            tk.Label(content_frame, text=group_key, bg="white", font=("Arial", 10), anchor="w").grid(row=i, column=0, padx=10, pady=5, sticky="w")

            # Destination Node
            dest_frame = tk.Frame(content_frame, bg="white")
            dest_frame.grid(row=i, column=1, padx=10, pady=5, sticky="w")

            dest_button = tk.Button(dest_frame, text="Select Destination", command=lambda idx=i: self.select_destination(idx))
            dest_button.pack(side="left")
            dest_label = tk.Label(dest_frame, text="", bg="white", font=("Arial", 10), fg="grey")
            dest_label.pack(side="left", padx=5)

            self.destination_paths[i] = {"label": dest_label, "files": items}

        # Footer
        footer_frame = tk.Frame(self.main_frame, bg="white")
        footer_frame.pack(fill="x", pady=10)

        # Size check checkbox
        tk.Checkbutton(
            footer_frame,
            text="Check Size",
            variable=self.size_check_enabled,
            bg="white",
            font=("Arial", 12)
        ).pack(side="left", padx=10)

        # Run button
        tk.Button(footer_frame, text="RUN", command=self.run_process).pack(side="left", padx=10)

    def show_popup(self, message):
        """Show a popup window with a message."""
        popup = tk.Toplevel(self)
        popup.title("Processing")
        popup.geometry("300x100")
        popup.transient(self)
        popup.grab_set()
        tk.Label(popup, text=message, font=("Arial", 12)).pack(pady=30)
        return popup

    def select_destination(self, idx):
        """Open a dialog for selecting a destination folder."""
        folder = filedialog.askdirectory()
        if folder:
            self.destination_paths[idx]["label"].config(text=folder)
            self.destination_paths[idx]["path"] = folder

    def run_process(self):
        """Run the file copying process."""
        summary = {"success": 0, "insufficient_space": 0, "size_differences": 0}

        popup = self.show_popup("Transferring Files...")
        for idx, data in self.destination_paths.items():
            if "path" in data and data["path"]:
                destination_folder = data["path"]
                os.makedirs(destination_folder, exist_ok=True)

                total_size_source = sum(os.path.getsize(file["path"]) for file in data["files"])
                total_size_dest = 0

                # Check if there's enough space in the destination
                if self.size_check_enabled.get():
                    free_space = shutil.disk_usage(destination_folder).free
                    if free_space < total_size_source:
                        summary["insufficient_space"] += 1
                        messagebox.showwarning(
                            "Insufficient Space",
                            f"Not enough space for group: {data['label'].cget('text')}",
                        )
                        continue

                # Copy files
                for file_data in data["files"]:
                    shutil.copy(file_data["path"], destination_folder)
                    total_size_dest += os.path.getsize(file_data["path"])

                # Compare sizes
                if total_size_source != total_size_dest:
                    summary["size_differences"] += 1

                summary["success"] += 1

        popup.destroy()

        # Show summary
        messagebox.showinfo(
            "Summary",
            f"{summary['success']} groups transferred successfully\n"
            f"{summary['insufficient_space']} groups didn't have sufficient space\n"
            f"{summary['size_differences']} groups have size differences",
        )


if __name__ == "__main__":
    app = App()
    app.mainloop()
