import os
import shutil
import exifread
import concurrent.futures
from tqdm import tqdm
import datetime
import time

def extract_camera_model(file_path):
    """
    Extracts the camera model from an image file's EXIF metadata.
    Returns the camera model string if found, otherwise None.
    """
    try:
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            camera_model = tags.get('Image Model')
            if camera_model:
                return str(camera_model).strip()
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    return None

def get_file_date(file_path, ext, photo_extensions):
    """
    Returns a datetime object representing the file's date.
    For photos in supported formats, attempts to use the EXIF DateTimeOriginal.
    Falls back to the file's modification time if not available.
    """
    if ext in photo_extensions:
        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
                date_tag = tags.get('EXIF DateTimeOriginal')
                if date_tag:
                    # Expected format: "YYYY:MM:DD HH:MM:SS"
                    date_str = str(date_tag)
                    return datetime.datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
        except Exception as e:
            print(f"Error reading EXIF date from {file_path}: {e}")
    # Fallback: file modification time
    mod_time = os.path.getmtime(file_path)
    return datetime.datetime.fromtimestamp(mod_time)

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def secure_copy(source_file_path, target_file_path):
    """
    Securely copies a file from source to destination,
    preserving metadata and verifying the file size.
    Returns True if successful, otherwise False.
    """
    try:
        shutil.copy2(source_file_path, target_file_path)
        if os.path.getsize(source_file_path) == os.path.getsize(target_file_path):
            return True
        else:
            print(f"Warning: Size mismatch for {os.path.basename(source_file_path)}")
            return False
    except Exception as e:
        print(f"Error copying {source_file_path} to {target_file_path}: {e}")
        return False

def process_file(task):
    """
    Processes a single file by copying it to the appropriate destination folder.
    Expects task to be a tuple:
      (root, file_name, photography_main, videography_main, photo_exts, video_exts)
    Returns a tuple (success, file_name).
    """
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
    target_file_path = os.path.join(target_folder, file_name)
    # Secure copy with verification
    success = secure_copy(source_file_path, target_file_path)
    return (success, file_name)

def parse_date_input(date_input):
    """
    Parses the date input from the user.
    Accepts either a single date ("DD/MM/YYYY") or a range ("DD/MM/YYYY - DD/MM/YYYY").
    Returns a tuple (start_date, end_date) if parsing is successful,
    otherwise returns (None, None).
    """
    try:
        # Allow for different dash characters and spacing
        if '-' in date_input:
            # Replace any en dash or em dash with a standard dash
            for dash in ['–', '—']:
                date_input = date_input.replace(dash, '-')
            # Try splitting on ' - ' first, otherwise just on '-'
            if ' - ' in date_input:
                parts = date_input.split(' - ')
            else:
                parts = date_input.split('-')
            if len(parts) != 2:
                raise ValueError("Invalid range format. Please use 'DD/MM/YYYY - DD/MM/YYYY'.")
            start_date = datetime.datetime.strptime(parts[0].strip(), "%d/%m/%Y").date()
            end_date = datetime.datetime.strptime(parts[1].strip(), "%d/%m/%Y").date()
        else:
            single_date = datetime.datetime.strptime(date_input.strip(), "%d/%m/%Y").date()
            start_date = end_date = single_date
        return start_date, end_date
    except Exception as e:
        print(f"Error parsing date input: {e}")
        return None, None

def main():
    # Get user inputs for folders and photographer name.
    source_folder = input("Enter the source folder path where your media files are located: ").strip()
    event_folder = input("Enter the destination event folder path (parent folder): ").strip()
    photographer_name = input("Enter your name: ").strip()

    photo_extensions = {'.jpg', '.jpeg', '.cr2', '.nef', '.arw', '.dng', '.cr3', '.raf', '.gpr'}
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv'}

    # Prompt for date or date range.
    date_input = input("Enter a date (DD/MM/YYYY) for one day or a date range (DD/MM/YYYY - DD/MM/YYYY), or leave empty for all files: ").strip()
    use_date_filter = False
    start_date = end_date = None
    if date_input:
        start_date, end_date = parse_date_input(date_input)
        if start_date and end_date:
            use_date_filter = True
        else:
            print("Continuing without date filtering due to input error.")

    # First pass: recursively scan for photo files (skipping files starting with '.' or '_')
    # to collect camera models from EXIF metadata.
    camera_models_found = set()
    print("Scanning for camera models in photo files. This may take a while...")
    for root, dirs, files in os.walk(source_folder):
        for file_name in files:
            if file_name.startswith('.') or file_name.startswith('_'):
                continue
            ext = os.path.splitext(file_name)[1].lower()
            if ext in photo_extensions:
                file_path = os.path.join(root, file_name)
                cam_model = extract_camera_model(file_path)
                if cam_model:
                    camera_models_found.add(cam_model)

    # Determine the chosen camera model for tagging video files.
    if not camera_models_found:
        chosen_camera_model = input("No camera model metadata found in photo files. Enter the camera model to tag video files: ").strip()
    elif len(camera_models_found) == 1:
        chosen_camera_model = list(camera_models_found)[0]
        print(f"Found one camera model: {chosen_camera_model}. It will be used for tagging video files.")
    else:
        print("Multiple camera models detected:")
        camera_models_list = list(camera_models_found)
        for idx, model in enumerate(camera_models_list, start=1):
            print(f"{idx}. {model}")
        while True:
            try:
                choice = int(input("Enter the number corresponding to the camera model you want to use for tagging video files: ").strip())
                if 1 <= choice <= len(camera_models_list):
                    chosen_camera_model = camera_models_list[choice - 1]
                    break
                else:
                    print("Invalid selection. Try again.")
            except ValueError:
                print("Please enter a valid number.")

    time.sleep(1)
    # Prepare folder suffix.
    folder_suffix = f"{chosen_camera_model}_{photographer_name}".replace(" ", "_")

    # Create the destination folder structure.
    graphics_folder = os.path.join(event_folder, "Graphics")
    photography_main = os.path.join(event_folder, "Photography", folder_suffix)
    create_directory(graphics_folder)
    create_directory(photography_main)

    # For videography, create the main folder directly under event_folder.
    videography_folder = os.path.join(event_folder, "Videography")
    create_directory(videography_folder)
    # Create three blank subfolders directly under Videography.
    create_directory(os.path.join(videography_folder, "EXPORT"))
    create_directory(os.path.join(videography_folder, "Project Files"))
    create_directory(os.path.join(videography_folder, "VFX + SFX Folder"))
    # Create the subfolder for transferred video files.
    videography_main = os.path.join(videography_folder, folder_suffix)
    create_directory(videography_main)

    time.sleep(1)
    # Build list of files to process (recursively), filtering by date if required.
    files_to_process = []
    for root, dirs, files in os.walk(source_folder):
        for file_name in files:
            if file_name.startswith('.') or file_name.startswith('_'):
                continue
            ext = os.path.splitext(file_name)[1].lower()
            file_path = os.path.join(root, file_name)
            if use_date_filter:
                file_date = get_file_date(file_path, ext, photo_extensions).date()
                if not (start_date <= file_date <= end_date):
                    continue
            files_to_process.append((root, file_name, photography_main, videography_main, photo_extensions, video_extensions))

    if use_date_filter:
        print(f"Found {len(files_to_process)} files to process based on the date filter ({start_date} to {end_date}).")
    else:
        print(f"Found {len(files_to_process)} files to process.")

    time.sleep(1)
    # Process files concurrently using ThreadPoolExecutor and display progress with tqdm.
    success_count = 0
    skipped_files = []
    with tqdm(total=len(files_to_process), desc="Processing Files", unit="file") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            future_to_file = {
                executor.submit(process_file, task): task for task in files_to_process
            }
            for future in concurrent.futures.as_completed(future_to_file):
                try:
                    success, file_name = future.result()
                    if success:
                        success_count += 1
                    else:
                        skipped_files.append(file_name)
                except Exception as exc:
                    root, file_name, *_ = future_to_file[future]
                    print(f"{file_name} generated an exception: {exc}")
                    skipped_files.append(file_name)
                pbar.update(1)

    # Output summary of transfers.
    print("\nTransfer Summary:")
    print(f"Successfully transferred {success_count} files, skipped {len(skipped_files)} files:")
    for file in skipped_files:
        print(file)

if __name__ == "__main__":
    main()
