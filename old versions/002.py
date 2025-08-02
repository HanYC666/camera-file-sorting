import os
from PIL import Image
from pymediainfo import MediaInfo
import pyexiv2
import rawpy
import pillow_heif

# Register HEIF opener for Pillow
pillow_heif.register_heif_opener()

# Supported image and video extensions
image_extensions = (
    '.jpg', '.jpeg', '.png', '.tiff', '.bmp', 
    '.heif', '.heic', '.arw', '.nef', '.cr2', '.cr3', '.dng'
)
video_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.hevc', '.flv', '.webm', '.mpg', '.mpeg')

def get_image_metadata(image_path):
    """Extract metadata from image file."""
    try:
        # Check if the image is HEIF/HEIC
        if image_path.lower().endswith(('heif', 'heic')):
            # Open the image using Pillow (which will now use pillow-heif for HEIF/HEIC)
            image = Image.open(image_path)
            metadata = {
                'Camera Model': image.info.get('model', 'N/A'),
                'Camera Serial': image.info.get('serial_number', 'N/A'),
                'Photographer': image.info.get('artist', 'N/A'),
                'Owner': image.info.get('copyright', 'N/A')
            }
            return metadata
        
        # For other image formats like jpg, png, etc., try using Pillow first
        image = Image.open(image_path)
        exif_data = image._getexif()  # Use Pillow's built-in EXIF extraction
        
        # Default values for missing fields
        camera_model = 'N/A'
        camera_serial = 'N/A'
        photographer = 'N/A'
        owner = 'N/A'
        
        if exif_data:
            camera_model = exif_data.get(0x0110, 'N/A')  # 0x0110 is the tag for Camera Model
            camera_serial = exif_data.get(0x0310, 'N/A')  # Serial number (if available)
            photographer = exif_data.get(0x0131, 'N/A')  # Artist (Photographer)
            owner = exif_data.get(0x8298, 'N/A')  # Copyright (Owner)
        
        metadata = {
            'Camera Model': camera_model,
            'Camera Serial': camera_serial,
            'Photographer': photographer,
            'Owner': owner
        }
        
        return metadata
    except Exception as e:
        print(f"Error reading image: {e}")
        return {}

def get_raw_image_metadata(image_path):
    """Extract metadata from RAW image files (ARW, NEF, CR2, CR3, DNG)."""
    try:
        # Check if the image file has EXIF metadata (Canon CR2, CR3, Sony ARW, Nikon NEF, etc.)
        metadata = {}
        
        # Use pyexiv2 for EXIF data extraction (Camera Model, Serial, etc.)
        try:
            image = pyexiv2.Image(image_path)
            image.read_metadata()
            
            metadata['Camera Model'] = image.get_exif_metadata().get('Exif.Image.Model', 'N/A')
            metadata['Camera Serial'] = image.get_exif_metadata().get('Exif.Image.SerialNumber', 'N/A')
            metadata['Photographer'] = image.get_exif_metadata().get('Exif.Image.Artist', 'N/A')
            metadata['Owner'] = image.get_exif_metadata().get('Exif.Image.Copyright', 'N/A')

            return metadata
        except Exception as exiv2_error:
            print(f"Error reading EXIF data using pyexiv2: {exiv2_error}")
        
        # If EXIF fails, fall back to rawpy for pixel data (but no metadata)
        try:
            if image_path.lower().endswith(('cr2', 'cr3', 'arw', 'nef', 'dng')):
                with rawpy.imread(image_path) as raw:
                    # rawpy doesn't provide metadata like camera model/serial directly
                    metadata['Camera Model'] = 'N/A'  # Rawpy doesn't provide this directly
                    metadata['Camera Serial'] = 'N/A'
                    metadata['Photographer'] = 'N/A'
                    metadata['Owner'] = 'N/A'

                return metadata
        except Exception as rawpy_error:
            print(f"Error reading raw image using rawpy: {rawpy_error}")
        
        return {}
    except Exception as e:
        print(f"Error reading raw image: {e}")
        return {}

def get_video_metadata(video_path):
    """Extract metadata from video file."""
    try:
        # Parse the video file
        media_info = MediaInfo.parse(video_path)
        
        if not media_info.tracks:
            return {'Error': 'No metadata found in this video.'}

        # Extract general metadata
        general_track = media_info.general_tracks[0] if media_info.general_tracks else None
        
        # Extract video metadata
        video_track = media_info.video_tracks[0] if media_info.video_tracks else None
        
        video_metadata = {
            'File Format': general_track.format if general_track else 'N/A',
            'Duration (s)': general_track.duration if general_track else 'N/A',
            'Video Codec': video_track.codec if video_track else 'N/A',
            'Resolution': f"{video_track.width}x{video_track.height}" if video_track else 'N/A',
            'Frame Rate': video_track.frame_rate if video_track else 'N/A',
            'Bitrate': video_track.bit_rate if video_track else 'N/A',
            'Camera Model': general_track.tag_string if general_track else 'N/A',
            'Owner': general_track.encoded_by if general_track else 'N/A'
        }
        
        return video_metadata
    except Exception as e:
        print(f"Error reading video: {e}")
        return {}

def print_metadata(file_path):
    """Print metadata based on the file type (image/video)."""
    if file_path.lower().endswith(image_extensions):
        print(f"Image Metadata for {file_path}:")
        if file_path.lower().endswith(('.arw', '.nef', '.cr2', '.cr3', '.dng')):
            metadata = get_raw_image_metadata(file_path)
        else:
            metadata = get_image_metadata(file_path)
        if not metadata:
            print("Error reading image metadata.")
        else:
            for key, value in metadata.items():
                print(f"{key}: {value}")
    elif file_path.lower().endswith(video_extensions):
        print(f"Video Metadata for {file_path}:")
        metadata = get_video_metadata(file_path)
        if not metadata:
            print("Error reading video metadata.")
        else:
            for key, value in metadata.items():
                print(f"{key}: {value}")
    else:
        print(f"Unsupported file format: {file_path}")

def scan_directory(directory_path):
    """Recursively scan a directory for image and video files and output their metadata."""
    for root, _, files in os.walk(directory_path):
        for file in files:
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
