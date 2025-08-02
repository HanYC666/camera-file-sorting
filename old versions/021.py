import os
import shutil
import exifread

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

def get_user_input(prompt):
    return input(prompt)

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def main():
    # Get user inputs
    print("Enter the source folder path where your media files are located:")
    source_folder = get_user_input("").strip()
    print("Enter the destination event folder path (parent folder):")
    event_folder = get_user_input("").strip()
    print("Enter your name:")
    photographer_name = get_user_input("").strip()

    # Define allowed file extensions (all in lowercase)
    photo_extensions = {'.jpg', '.jpeg', '.cr2', '.nef', '.arw', '.dng', '.raf', 'gpr'}
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv'}

    # First pass: recursively scan for photo files (skipping files that start with '.' or '_')
    # and collect camera models from their EXIF metadata.
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

    # Determine the chosen camera model for video tagging
    if not camera_models_found:
        print("No camera model metadata found in photo files.")
        chosen_camera_model = get_user_input("Please enter the camera model to tag video files: ").strip()
    elif len(camera_models_found) == 1:
        chosen_camera_model = list(camera_models_found)[0]
        print(f"Found one camera model: {chosen_camera_model}. It will be used for tagging video files.")
    else:
        print("Multiple camera models detected:")
        camera_models_list = list(camera_models_found)
        for idx, model in enumerate(camera_models_list, start=1):
            print(f"{idx}. {model}")
        while True:
            choice = get_user_input("Enter the number corresponding to the camera model you want to use for tagging video files: ").strip()
            try:
                choice_index = int(choice) - 1
                if 0 <= choice_index < len(camera_models_list):
                    chosen_camera_model = camera_models_list[choice_index]
                    break
                else:
                    print("Invalid selection. Try again.")
            except ValueError:
                print("Please enter a valid number.")

    # Prepare the folder name using the chosen camera model and photographer name.
    folder_suffix = f"{chosen_camera_model}_{photographer_name}".replace(" ", "_")

    # Create the destination folder structure:
    # <event_folder>/
    #    Graphics/
    #    Photography/<folder_suffix>/
    #         (subfolders for photo file types)
    #    Videography/<folder_suffix>/
    #         (subfolders for video file types)
    graphics_folder = os.path.join(event_folder, "Graphics")
    photography_main = os.path.join(event_folder, "Photography", folder_suffix)
    videography_main = os.path.join(event_folder, "Videography", folder_suffix)

    create_directory(graphics_folder)
    create_directory(photography_main)
    create_directory(videography_main)

    # Second pass: recursively scan for all files to process transfers.
    # We build a list of files first to avoid issues with moving files during iteration.
    files_to_process = []
    for root, dirs, files in os.walk(source_folder):
        for file_name in files:
            if file_name.startswith('.') or file_name.startswith('_'):
                continue
            files_to_process.append((root, file_name))

    # Process each file
    for root, file_name in files_to_process:
        ext = os.path.splitext(file_name)[1].lower()
        source_file_path = os.path.join(root, file_name)
        # Process photo files
        if ext in photo_extensions:
            folder_name = ext[1:].upper()  # e.g. 'jpg' becomes 'JPG'
            target_folder = os.path.join(photography_main, folder_name)
            create_directory(target_folder)
            target_file_path = os.path.join(target_folder, file_name)
            print(f"Moving photo {file_name} to {target_folder}")
            shutil.move(source_file_path, target_file_path)
        # Process video files
        elif ext in video_extensions:
            folder_name = ext[1:].upper()
            target_folder = os.path.join(videography_main, folder_name)
            create_directory(target_folder)
            target_file_path = os.path.join(target_folder, file_name)
            print(f"Moving video {file_name} to {target_folder}")
            shutil.move(source_file_path, target_file_path)
        else:
            print(f"Skipping file {file_name}: unsupported file type.")

if __name__ == "__main__":
    main()
