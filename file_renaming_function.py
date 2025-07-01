import os
import shutil

def rename_and_copy_images(root_folder, target_folder):
    # Ensure the target directory exists
    os.makedirs(target_folder, exist_ok=True)

    # Walk through the root folder
    for date_folder in os.listdir(root_folder):
        date_folder_path = os.path.join(root_folder, date_folder)
        
        # Ensure it's a directory
        if os.path.isdir(date_folder_path):
            for individual_folder in os.listdir(date_folder_path):
                individual_folder_path = os.path.join(date_folder_path, individual_folder)
                
                # Ensure it's a directory
                if os.path.isdir(individual_folder_path):
                    # List all files in the individual folder
                    images = os.listdir(individual_folder_path)
                    
                    # Initialize a counter for image numbering
                    count = 1
                    
                    for image_name in images:
                        # Get the file extension
                        _, ext = os.path.splitext(image_name)
                        
                        # Create the new image name
                        new_image_name = f"{date_folder}_{individual_folder}_{count}{ext}"
                        
                        # Get the full path for the old image name
                        old_image_path = os.path.join(individual_folder_path, image_name)
                        
                        # Get the full path for the new image name in the target directory
                        new_image_path = os.path.join(target_folder, new_image_name)
                        
                        # Copy and rename the image to the target directory
                        shutil.copy2(old_image_path, new_image_path)
                        
                        # Increment the counter
                        count += 1

# Example usage
root_folder = 'path/to/root_folder'
target_folder = 'path/to/target_folder'
rename_and_copy_images(root_folder, target_folder)
