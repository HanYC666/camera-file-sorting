# This file is part of the camera-file-sorting program
# Copyright (C) Yichen Han 2025
# Licensed under the GNU AGPL v3.0 (see LICENSE)
# Public users must provide credit as stated in the "LICENSE" file

import os
import io
import json
import shutil
import subprocess
import concurrent.futures
from tqdm import tqdm
import datetime
import time

def exiftool_get_metadata(file_path):
    """
    Uses ExifTool to extract Model and DateTimeOriginal in JSON format.
    Returns a dict with keys 'model' (str) and 'datetime_original' (datetime) if found, else None.
    """
    try:
        # Only request the tags we need, for speed
        cmd = ["exiftool", "-j", "-n", "-Model", "-DateTimeOriginal", file_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # ExifTool error
            return None

        data = json.loads(result.stdout)
        if not data or len(data) == 0:
            return None

        info = data[0]
        camera_model = info.get("Model")
        dt_original_str = info.get("DateTimeOriginal")

        # Convert "YYYY:MM:DD HH:MM:SS" -> datetime
        dt_original = None
        if dt_original_str:
            for fmt in ["%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                try:
                    dt_original = datetime.datetime.strptime(dt_original_str, fmt)
                    break
                except ValueError:
                    pass

        return {
            "model": camera_model,
            "datetime_original": dt_original
        }

    except Exception as e:
        print(f"Error extracting metadata from {file_path}: {e}")
        return None

def extract_camera_model(file_path):
    """
    Returns the camera model if found, otherwise None.
    """
    meta = exiftool_get_metadata(file_path)
    if meta and meta["model"]:
        return meta["model"].strip()
    return None

def get_file_date(file_path, ext, photo_extensions):
    """
    Returns a datetime object for the file:
      1) DateTimeOriginal from ExifTool if available
      2) Otherwise, file modification time
    """
    if ext in photo_extensions:
        meta = exiftool_get_metadata(file_path)
        if meta and meta["datetime_original"]:
            return meta["datetime_original"]
    # Fallback: file modification time
    mod_time = os.path.getmtime(file_path)
    return datetime.datetime.fromtimestamp(mod_time)

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def secure_copy(source_file_path, target_file_path):
    """
    Copy the file, preserving metadata, and verify size matches.
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
    Copies one file to the correct folder (Photography or Videography).
    Returns (success_bool, file_name).
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
    success = secure_copy(source_file_path, target_file_path)
    return (success, file_name)

def parse_date_input(date_input):
    """
    Parses a single date "DD/MM/YYYY" or a range "DD/MM/YYYY - DD/MM/YYYY".
    Returns (start_date, end_date) or (None, None) if error.
    """
    try:
        if '-' in date_input:
            for dash in ['–', '—']:
                date_input = date_input.replace(dash, '-')
            parts = date_input.split(' - ') if ' - ' in date_input else date_input.split('-')
            if len(parts) != 2:
                raise ValueError("Invalid range format. Use 'DD/MM/YYYY - DD/MM/YYYY'.")
            start_date = datetime.datetime.strptime(parts[0].strip(), "%d/%m/%Y").date()
            end_date = datetime.datetime.strptime(parts[1].strip(), "%d/%m/%Y").date()
        else:
            single_date = datetime.datetime.strptime(date_input.strip(), "%d/%m/%Y").date()
            start_date = end_date = single_date
        return start_date, end_date
    except Exception as e:
        print(f"Error parsing date input: {e}")
        return None, None

def find_first_camera_model_in_parallel(photo_files):
    """
    Scans photo_files in parallel, returning the first camera model found.
    If none found, returns None.
    Once a model is found, cancels remaining tasks for speed.
    """
    if not photo_files:
        return None

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_file = {
            executor.submit(extract_camera_model, pf): pf
            for pf in photo_files
        }
        for future in concurrent.futures.as_completed(future_to_file):
            model = future.result()
            if model:
                # Found a model; stop scanning further
                if hasattr(executor, 'shutdown'):
                    # Python 3.9+ only
                    executor.shutdown(cancel_futures=True)
                return model
    return None

def main():
    source_folder = input("Enter the source folder path where your media files are located: ").strip()
    event_folder = input("Enter the destination event folder path (parent folder): ").strip()
    photographer_name = input("Enter your name: ").strip()

    photo_extensions = {'.jpg', '.jpeg', '.cr2', '.nef', '.arw', '.dng', '.cr3', '.raf', '.gpr'}
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv'}

    date_input = input("Enter a date (DD/MM/YYYY) for one day or a range (DD/MM/YYYY - DD/MM/YYYY), or leave empty for all files: ").strip()
    use_date_filter = False
    start_date = end_date = None
    if date_input:
        start_date, end_date = parse_date_input(date_input)
        if start_date and end_date:
            use_date_filter = True
        else:
            print("Continuing without date filtering due to input error.")

    # 1) Gather photo files for camera-model scanning
    print("Gathering photo files for camera-model detection...")
    photo_file_paths = []
    for root, dirs, files in os.walk(source_folder):
        for file_name in files:
            if file_name.startswith('.') or file_name.startswith('_'):
                continue
            ext = os.path.splitext(file_name)[1].lower()
            if ext in photo_extensions:
                photo_file_paths.append(os.path.join(root, file_name))

    # 2) Find the first camera model in parallel
    print("Scanning for the first camera model in photo files...")
    camera_model = find_first_camera_model_in_parallel(photo_file_paths)
    if not camera_model:
        # If we didn't find any, ask the user
        camera_model = input("No camera model found. Enter the camera model to tag video files: ").strip()
    else:
        print(f"Found camera model: {camera_model}")

    time.sleep(1)
    folder_suffix = f"{camera_model}_{photographer_name}".replace(" ", "_")

    # Always create a Graphics folder
    graphics_folder = os.path.join(event_folder, "Graphics")
    create_directory(graphics_folder)

    # Prepare destination paths for photos & videos
    photography_main = os.path.join(event_folder, "Photography", folder_suffix)
    videography_main = os.path.join(event_folder, "Videography", folder_suffix)

    # 3) Build the list of files to process (photo + video)
    print("Building file list for transfer...")
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

            files_to_process.append(
                (root, file_name, photography_main, videography_main, photo_extensions, video_extensions)
            )

    # Create main folders only if needed
    photo_files = [f for f in files_to_process if os.path.splitext(f[1])[1].lower() in photo_extensions]
    video_files = [f for f in files_to_process if os.path.splitext(f[1])[1].lower() in video_extensions]

    if photo_files:
        create_directory(photography_main)
    if video_files:
        videography_folder = os.path.join(event_folder, "Videography")
        create_directory(videography_folder)
        create_directory(videography_main)
        create_directory(os.path.join(videography_folder, "EXPORT"))
        create_directory(os.path.join(videography_folder, "Project Files"))
        create_directory(os.path.join(videography_folder, "VFX + SFX Folder"))

    time.sleep(1)
    print(f"Found {len(files_to_process)} files to process.")

    # 4) Transfer files in parallel
    success_count = 0
    skipped_files = []
    time.sleep(1)
    with tqdm(total=len(files_to_process), desc="Processing Files", unit="file") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            future_to_file = {
                executor.submit(process_file, task): task
                for task in files_to_process
            }
            for future in concurrent.futures.as_completed(future_to_file):
                try:
                    success, file_name = future.result()
                    if success:
                        success_count += 1
                    else:
                        skipped_files.append(file_name)
                except Exception:
                    skipped_files.append(file_name)
                pbar.update(1)

    print("\nTransfer Summary:")
    print(f"Successfully transferred {success_count} files, skipped {len(skipped_files)} files.")
    if skipped_files:
        print("Skipped files:")
        for file in skipped_files:
            print(file)

    print("\nTransfer complete. Press any key to exit...")
    input()

if __name__ == "__main__":
    main()
