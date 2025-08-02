import os
import subprocess
import json

# Supported image and video extensions
image_extensions = (
    '.jpg', '.jpeg', '.png', '.tiff', '.bmp', 
    '.heif', '.heic', '.arw', '.nef', '.cr2', '.cr3', '.dng'
)
video_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.hevc', '.flv', '.webm', '.mpg', '.mpeg')

# List of metadata fields to output
fields_to_output = [
    'FileName', 'FileSize', 'ImageWidth', 'ImageHeight', 'Make', 'Model', 'Artist', 
    'Copyright', 'ExposureTime', 'FNumber', 'ExposureProgram', 'ISO', 
    'DateTimeOriginal', 'ShutterSpeedValue', 'ApertureValue', 'Flash', 
    'FocalLength', 'SerialNumber', 'LensSerialNumber', 'LensType', 'LensModel', 
    'InternalSerialNumber', 'AspectRatio'
]

def get_metadata_with_exiftool(file_path):
    """Use ExifTool to get metadata from image or video files."""
    try:
        # Call exiftool using subprocess (assuming exiftool.exe is in the same folder as this script)
        command = ['./exiftool.exe', '-json', file_path]
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        # Parse the output JSON
        metadata = json.loads(result.stdout)
        
        # Return the first entry (ExifTool outputs a list)
        if metadata:
            return metadata[0]
        else:
            print(f"Error: No metadata found for {file_path}")
            return {}
    except subprocess.CalledProcessError as e:
        print(f"Error executing ExifTool: {e}")
        return {}
    except Exception as e:
        print(f"Error reading metadata: {e}")
        return {}

def print_metadata(file_path):
    """Print filtered metadata based on the file type (image/video)."""
    if file_path.lower().endswith(image_extensions):
        print(f"Image Metadata for {file_path}:")
    elif file_path.lower().endswith(video_extensions):
        print(f"Video Metadata for {file_path}:")
    else:
        print(f"Unsupported file format: {file_path}")
        return

    metadata = get_metadata_with_exiftool(file_path)
    
    if not metadata:
        print("Error reading metadata.")
    else:
        # Iterate over the selected fields and print their values
        for field in fields_to_output:
            value = metadata.get(field, 'N/A')  # Default to 'N/A' if the field is not available
            print(f"{field}: {value}")

def scan_directory(directory_path):
    """Recursively scan a directory for image and video files and output their metadata."""
    for root, _, files in os.walk(directory_path):
        for file in files:
            # Skip files that start with a dot (e.g., .DS_Store, .thumbs.db)
            if file.startswith('.'):
                continue
            
            file_path = os.path.join(root, file)
            print_metadata(file_path)

if __name__ == "__main__":
    # Ask the user for the directory path
    directory_path = input("Enter the directory path (image/video): ").strip()

    if os.path.isdir(directory_path):
        print(f"Scanning directory: {directory_path}")
        scan_directory(directory_path)
    else:
        print("The provided directory path does not exist.")
