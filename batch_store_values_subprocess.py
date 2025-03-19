import os
import datetime
from datetime import date
import cv2 as cv
import numpy as np
import pandas as pd
from pathlib import Path
import multiprocessing
import shutil
import sys

########################################################################################################################
########################################## GUI-DEFINED PATHS AND VALUES ################################################
BASE_DIR = Path(sys.argv[1])
directory = sys.argv[2]
detectors = sys.argv[3:]  # All remaining arguments are detectors
# Load user-set parameters for fingerprint extraction
df = pd.read_csv(os.path.join(BASE_DIR, "data/user_parameters.csv"))
# Convert to dictionary (keys = parameters, values = converted numbers)
params = {row["Parameter"]: float(row["Value"]) for _, row in df.iterrows()}
hessian_threshold = int(params["hessian_threshold"]) # how strict I am about the size of keypoints for SURF.
akaze_threshold = float(params["akaze_threshold"]) # how strict I am about the size of keypoints for AKAZE.
n_features = int(params["n_features"]) # how many keypoints to extract from SIFT and ORB objects. 1000 is default.
########################################################################################################################


########################################################################################################################
########################################### MANUALLY DEFINE PATHS AND VALUES ###########################################
# Define base project directory
#BASE_DIR = Path.home() / "Documents/Project_name"

# Define the target project subdirectory (choose either "temp" or "fingerprints")
#directory = "fingerprints"

# Choose which fingerprint detectors to use, delete as appropriate. SURF may not be available on all devices.
#detectors = ['akaze_fingerprint', 'orb_fingerprint', 'sift_fingerprint', 'surf_fingerprints']

#hessian_threshold = int(500)
#n_features = int(1000)
########################################################################################################################


########################################################################################################################
# List and print all files in directory. fingerprints will be extracted from these images
images_list = os.listdir(BASE_DIR / directory)
########################################################################################################################


########################################################################################################################
# initialise only the chosen detectors - SURF may not be available on all devices
if 'surf_fingerprint' in detectors:
    surf = cv.xfeatures2d.SURF_create(hessian_threshold)
if 'sift_fingerprint' in detectors:
    sift = cv.SIFT_create(nfeatures=n_features)
if 'orb_fingerprint' in detectors:
    orb = cv.ORB_create(nfeatures=n_features)
if 'akaze_fingerprint' in detectors:
    akaze = cv.AKAZE_create(threshold = akaze_threshold)
########################################################################################################################


########################################################################################################################
# Define fingerprint-extraction and saving functions
def gen_surf_features(img, name, type, surf):
    surf_kp, surf_desc = surf.detectAndCompute(img, None)
    destination = BASE_DIR / directory / name
    np.savetxt(destination / f"{name}_surf_{type}.txt", surf_desc)
    return
def gen_sift_features(img, name, type, sift):
    sift_kp, sift_desc = sift.detectAndCompute(img, None)
    destination = BASE_DIR / directory / name
    np.savetxt(destination / f"{name}_sift_{type}.txt", sift_desc)
    return
def gen_orb_features(img, name, type, orb):
    orb_kp, orb_desc = orb.detectAndCompute(img, None) # ADD ERROR EXCEPTION HERE
    destination = BASE_DIR / directory / name
    np.savetxt(destination / f"{name}_orb_{type}.txt", orb_desc)
    return
def gen_akaze_features(img, name, type, akaze):
    akaze_kp, akaze_desc = akaze.detectAndCompute(img, None) # ADD ERROR EXCEPTION HERE
    destination = BASE_DIR / directory / name
    np.savetxt(destination / f"{name}_akaze_{type}.txt", akaze_desc)
    return
########################################################################################################################


########################################################################################################################
# a convenience function that moves problematic images to relevant error folder
def relocate(image_name):
    """Moves an image to the 'processing_errors/fingerprinting' directory."""
    new_folder_path = BASE_DIR / "processing_errors"/ "fingerprinting" / image_name
    try:
    # move the folder to a new location
        source_folder_path = BASE_DIR / directory / image_name
        shutil.move(source_folder_path, new_folder_path)
    except Exception as e:
        print(f"An error occurred while relocating {image_name}: {str(e)}")
        error_log_file = BASE_DIR / "logs" / "fingerprinting_error_logs.txt"
        with open(error_log_file, 'a') as f:
            f.write(f'\nAn error occurred while relocating {image_name}: {str(e)} \n')
########################################################################################################################


########################################################################################################################
# the main workhorse of this script, generates and then saves the chosen fingerprint types, with informative error logging
def process_image(image_name):
    try:
        # define path to image
        image_path = BASE_DIR / directory / image_name / f"{image_name}_mask.png"
        # Read the mask - path must be passed as a string
        mask1 = cv.imread(str(image_path))
        print(f"Working on {image_name}. Mask shape: {mask1.shape}")
    except:
        relocate(image_name)
        print(f"This image may not exist - {image_name}")
        error_log_file = BASE_DIR / "logs" / "fingerprinting_error_logs.txt"
        with open(error_log_file, 'a') as f:
            f.write(f'\n{image_name}. This image may not exist. Please check file. \n')
        return

    # Dictionary mapping detector names to their corresponding functions
    detector_functions = {
        'surf_fingerprint': lambda: gen_surf_features(mask1, image_name, "mask", surf),
        'sift_fingerprint': lambda: gen_sift_features(mask1, image_name, "mask", sift),
        'orb_fingerprint': lambda: gen_orb_features(mask1, image_name, "mask", orb),
        'akaze_fingerprint': lambda: gen_akaze_features(mask1, image_name, "mask", akaze)
    }

    # Process only the selected detectors
    for detector in detectors:
        try:
            print(f"Applying {detector} to {image_name}")
            detector_functions[detector]()

        except Exception as e:
            relocate(image_name)
            print(f"Error extracting {detector} fingerprints from {image_name}: {str(e)}")

            error_log_file = BASE_DIR / "logs" / "fingerprinting_error_logs.txt"
            with open(error_log_file, 'a') as f:
                f.write(f'\nError extracting {detector} fingerprints from {image_name}: {str(e)}. Please check file.\n')
########################################################################################################################


########################################################################################################################
# parallel processing the above function to speed things along.
def gen_fingerprints(images_list):
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(process_image, images_list)
    pool.close()
    pool.join()
########################################################################################################################


if __name__ == '__main__':
    # a clunky way to record processing times
    start_time = datetime.datetime.now()

    #pre-empt error logging
    error_log_file = BASE_DIR / "logs" / "fingerprinting_error_logs.txt"
    with open(error_log_file, 'a') as f:
        f.write(
            f'\n{datetime.datetime.now()} - Extracting fingerprints from images \n')

    # run the functions, do the things
    gen_fingerprints(images_list)

    # still a clunky way to record processing times, but effective
    processing_time = datetime.datetime.now() - start_time
    print("Time taken: ", processing_time)

    timing_log_file = BASE_DIR / "logs" / "processing_times.txt"
    with open(timing_log_file, 'a') as f:
        f.write(f'\nFingerprint extraction - {len(images_list)} files processed in {processing_time}. {date.today()} \n')