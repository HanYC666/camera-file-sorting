import os
import subprocess
import json
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# Define the metadata fields to display
fields_to_output = [
    'FileName', 'FileSize', 'ImageWidth', 'ImageHeight', 'Make', 'Model', 'Artist', 
    'Copyright', 'ExposureTime', 'FNumber', 'ExposureProgram', 'ISO', 
    'DateTimeOriginal', 'ShutterSpeedValue', 'ApertureValue', 'Flash', 
    'FocalLength', 'SerialNumber', 'LensSerialNumber', 'LensType', 'LensModel', 
    'InternalSerialNumber', 'AspectRatio'
]

# Define the file extensions supported
image_extensions = ('.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.heif', '.heic', '.arw', '.nef', '.cr2', '.cr3', '.dng', '.raf', '.gpr')
video_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.hevc', '.flv', '.webm', '.mpg', '.mpeg')

# Function to fetch metadata using ExifTool (must have ExifTool installed)
def get_metadata_with_exiftool(file_path):
    try:
        command = ['./exiftool', '-json', file_path]  # ExifTool command to get metadata
        result = subprocess.run(command, capture_output=True, text=True)
        metadata = json.loads(result.stdout)[0]
        return metadata
    except Exception as e:
        return None

# Function to get file metadata and add it to a list
def scan_files_in_directory(directory_path):
    file_data = []

    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.startswith('.'):
                continue  # Skip hidden files
            file_path = os.path.join(root, file)
            file_extension = os.path.splitext(file)[1].lower()

            if file_extension in image_extensions or file_extension in video_extensions:
                metadata = get_metadata_with_exiftool(file_path)
                if metadata:
                    row_data = {field: metadata.get(field, 'N/A') for field in fields_to_output}
                    row_data['FileName'] = file
                    row_data['FileSize'] = os.path.getsize(file_path)
                    file_data.append(row_data)

    return file_data

# Function to create the Tkinter GUI window
def create_gui_table(file_data):
    # Create the main window
    root = tk.Tk()
    root.title("Metadata Table")
    
    # Set window size and position
    root.geometry("1200x800")

    # Create the treeview (table) widget
    columns = ['Data Type'] + [f"File {i+1}" for i in range(len(file_data))]
    tree = ttk.Treeview(root, columns=columns, show="headings")

    # Define the rows as metadata fields
    tree["show"] = "headings"
    
    # Insert the column headers
    tree.heading('#1', text='Data Type', anchor="w")
    for idx, column in enumerate(tree["columns"][1:], 2):
        tree.heading(column, text=f"File {idx-1}", anchor="w")
        tree.column(column, width=150, anchor="w")

    # Insert the rows (metadata fields) and their values
    for field in fields_to_output:
        row_values = [field]  # The first column is the field name itself (e.g., FileName, ImageWidth, etc.)
        for j in range(len(file_data)):
            value = file_data[j].get(field, 'N/A')
            row_values.append(value)
        
        tree.insert('', 'end', text=field, values=row_values)

    # Create a scrollbar for the table
    scrollbar = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
    tree.config(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    # Configure the treeview to have solid lines and borders around each cell
    style = ttk.Style()
    style.configure("Treeview", borderwidth=1, relief="solid")
    style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
    
    # Pack the treeview widget
    tree.pack(expand=True, fill="both")

    # Start the Tkinter event loop
    root.mainloop()

# Main function to execute
def main():
    # Ask for directory input
    directory_path = input("Enter the directory path (image/video): ")

    if not os.path.isdir(directory_path):
        print("Invalid directory path!")
        return

    # Scan files and extract metadata
    file_data = scan_files_in_directory(directory_path)

    if not file_data:
        messagebox.showerror("No Files Found", "No supported image/video files found in the directory!")
        return

    # Create the GUI and display the table
    create_gui_table(file_data)

if __name__ == "__main__":
    main()
