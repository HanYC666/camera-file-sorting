import os
import shutil
import exifread
import concurrent.futures
from tqdm import tqdm  # Progress bar library

def extract_camera_model(file_path):
    """Extracts the camera model from an image file's EXIF metadata."""
    try:
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            camera_model = tags.get('Image Model')
            if camera_model:
                return str(camera_model).strip()
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    return None

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def secure_copy(source_file_path, target_file_path):
    """Securely copies a file and verifies size match."""
    try:
        shutil.copy2(source_file_path, target_file_path)
        if os.path.getsize(source_file_path) == os.path.getsize(target_file_path):
            return True
        else:
            print(f"Warning: Size mismatch in {os.path.basename(source_file_path)}")
            return False
    except Exception as e:
        print(f"Error copying {source_file_path}: {e}")
        return False

def process_file(task):
    """Processes a single file (copying and organizing)."""
    root, file_name, photography_main, videography_main, photo_exts, video_exts = task
    ext = os.path.splitext(file_name)[1].lower()
    source_file_path = os.path.join(root, file_name)

    if ext in photo_exts:
        target_folder = os.path.join(photography_main, ext[1:].upper())
    elif ext in video_exts:
        target_folder = os.path.join(videography_main, ext[1:].upper())
    else:
        return (False, file_name)

    create_directory(target_folder)
    success = secure_copy(source_file_path, os.path.join(target_folder, file_name))
    return (success, file_name)

def main():
    # User Inputs
    source_folder = input("Enter the source folder path: ").strip()
    event_folder = input("Enter the destination event folder path: ").strip()
    photographer_name = input("Enter your name: ").strip()

    photo_extensions = {'.jpg', '.jpeg', '.cr2', '.nef', '.arw', '.dng', '.cr3', '.raf', '.gpr'}
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv'}

    # Scan for Camera Models
    camera_models_found = set()
    print("Scanning for camera models in photo files...")
    for root, _, files in os.walk(source_folder):
        for file_name in files:
            if not file_name.startswith(('.', '_')) and os.path.splitext(file_name)[1].lower() in photo_extensions:
                cam_model = extract_camera_model(os.path.join(root, file_name))
                if cam_model:
                    camera_models_found.add(cam_model)

    # Let user choose the camera model for video files
    if not camera_models_found:
        chosen_camera_model = input("No metadata found. Enter the camera model manually: ").strip()
    else:
        chosen_camera_model = list(camera_models_found)[0] if len(camera_models_found) == 1 else \
            camera_models_found.pop()  # Default to first detected if multiple

    folder_suffix = f"{chosen_camera_model}_{photographer_name}".replace(" ", "_")
    graphics_folder = os.path.join(event_folder, "Graphics")
    photography_main = os.path.join(event_folder, "Photography", folder_suffix)
    videography_main = os.path.join(event_folder, "Videography", folder_suffix)
    create_directory(graphics_folder)
    create_directory(photography_main)
    create_directory(videography_main)

    # Collect files to process
    files_to_process = []
    for root, _, files in os.walk(source_folder):
        for file_name in files:
            if not file_name.startswith(('.', '_')):
                files_to_process.append((root, file_name, photography_main, videography_main, photo_extensions, video_extensions))

    # Use ThreadPoolExecutor with a progress bar
    success_count = 0
    skipped_files = []
    with tqdm(total=len(files_to_process), desc="Processing Files", unit="file") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            future_to_file = {executor.submit(process_file, task): task for task in files_to_process}
            for future in concurrent.futures.as_completed(future_to_file):
                success, file_name = future.result()
                if success:
                    success_count += 1
                else:
                    skipped_files.append(file_name)
                pbar.update(1)  # Update progress bar

    # Summary Output
    print(f"\nTransfer Summary:\nSuccessfully transferred {success_count} files, skipped {len(skipped_files)}:")
    for file in skipped_files:
        print(file)

if __name__ == "__main__":
    main()
