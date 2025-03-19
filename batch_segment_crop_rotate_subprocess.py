# General core use and image processing.
import os
import datetime
from datetime import date
from pathlib import Path
import pandas as pd
import numpy as np
import cv2 as cv
import multiprocessing
import sys


########################################################################################################################
########################################## GUI-DEFINED PATHS AND VALUES ################################################
BASE_DIR = Path(sys.argv[1])
directory = sys.argv[2]
# Load user-set parameters for cropping and rotating
df = pd.read_csv(BASE_DIR / "data/user_parameters.csv")
# Convert to dictionary (keys = parameters, values = converted numbers)
params = {row["Parameter"]: float(row["Value"]) for _, row in df.iterrows()}
# Extract HSV range as tuples
# Set HSV colour thresholds. H{0:180}, S{0:255}, V{0:255}. annoying format
lower = (int(params["hue_low"]), int(params["saturation_low"]), int(params["value_low"]))
upper = (int(params["hue_high"]), int(params["saturation_high"]), int(params["value_high"]))
# Assign other parameters (convert to correct types)
kernel_size = int(params["kernel_size"]) # Amount of blurring to apply. Unnecessary!
threshold_value = int(params["threshold_value"]) # Grey-scale threshold to split foreground and background
num_patches = int(params["num_patches"]) # how many elytral splodges we expect
min_area = int(params["min_area"]) # size cutoff for ignoring spurious foreground artefacts in images
mult = float(params["mult"])  # a scalar of how much of the image I want to include around the region of interest
# poorly cropped photos will be bigger than well-processed photos. cutoff is based on value of height*width.
# unprocessed photos > 6000000 px. processed photos < 3500000 px
cutoff_size = int(params["cutoff_size"])
########################################################################################################################


########################################################################################################################
########################################### MANUALLY DEFINE PATHS AND VALUES ###########################################
# Define base project directory
#BASE_DIR = Path.home() / "Documents/Project_name"

# Define the target subdirectory (choose either "temp" or "unprocessed_photos")
#directory = "unprocessed_photos"

# Set HSV colour thresholds. H{0:180}, S{0:255}, V{0:255}. annoying format
#lower = (10, 75, 75)
#upper = (45,255,255)
#kernel_size = 11  # Amount of blurring to apply. Affects contours and finished mask
#threshold_value = 50  # Grey-scale threshold to split foreground and background
#min_area = 7500  # size cutoff for ignoring spurious foreground artefacts in images
#num_patches = 4  # the maximum number of elytral splodges we expect
#mult = 1.1  # a scalar of how much of the image I want to include around the region of interest. too much may add noise
# poorly cropped photos will be bigger than well-processed photos. cutoff is based on value of height*width.
# unprocessed photos > 6000000. processed photos < 3500000
#cutoff_size = int(6000000)
########################################################################################################################


########################################################################################################################
# List and print all files in directory. accepts multiple photo formats.
images_list = os.listdir(BASE_DIR / directory)
########################################################################################################################

# a list for keeping track of progress
#loop_count = [] # removing may break something??


########################################################################################################################
# the primary functions for loading, processing and exporting images. too many! handles user-defined size-related issues
# that might indicate poor cropping
def read_image(BASE_DIR, directory, image_file):
    image_path = BASE_DIR / directory / image_file
    img = cv.imread(str(image_path))
    name = image_file.split('.')[0] #drop file extension
    return img, name

def correct_image_rotation(img):
    if img.shape[1] > img.shape[0]:
        img = cv.rotate(img, cv.ROTATE_90_COUNTERCLOCKWISE)
    return img

def apply_thresholds(img, lower, upper, kernel_size):
    hsv_img = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    mask = cv.inRange(hsv_img, lower, upper)
    focal_regions = cv.bitwise_and(img, img, mask=mask)
    blurred_regions = cv.medianBlur(focal_regions, kernel_size)
    return mask, blurred_regions

def find_contours(blurred_regions, threshold_value):
    img_gray = cv.cvtColor(blurred_regions, cv.COLOR_RGB2GRAY)
    ret, thresh = cv.threshold(img_gray, threshold_value, 255, cv.THRESH_BINARY)
    contours, hierarchy = cv.findContours(thresh, 1, 2)
    return contours

def filter_contours(img, mask, contours, min_area, num_patches):
    areas = [cv.contourArea(contour) for contour in contours]
    patches = [areas.index(k) for k in sorted(areas, reverse=True)][:num_patches]
    conts = []
    for p in patches:
        if areas[p] > min_area:
            conts.append(contours[p])
    # redefining our colour mask based on the above filtering - removes noise for pattern extraction.
    # Step 1: Create a blank mask to start fresh
    filled_mask = np.zeros_like(mask)

    # Step 2: Draw the filtered contours onto the new mask
    for contour in conts:
        cv.drawContours(filled_mask, [contour], -1, 255, thickness=-1)

    # Step 3: Apply the filled mask to the original image
    # Convert the single-channel mask to match the dimensions of the original image
    filtered_mask = cv.cvtColor(filled_mask, cv.COLOR_GRAY2BGR)

    # Use bitwise_and to apply the mask to the original image
    filtered_mask = cv.bitwise_and(img, filtered_mask)

    return conts, filtered_mask


def find_minimum_rotated_bounding_box(conts):
    length = len(conts)
    cont = np.vstack([conts[q] for q in range(length)])
    rect = cv.minAreaRect(cont)
    box = cv.boxPoints(rect)
    box = np.int32(box)
    return rect, box

def crop_and_rotate_image(filtered_mask, img, rect, box, mult):
    W = rect[1][0]
    H = rect[1][1]
    Xs = [r[0] for r in box]
    Ys = [s[1] for s in box]
    x1 = min(Xs)
    x2 = max(Xs)
    y1 = min(Ys)
    y2 = max(Ys)

    rotated = False
    angle = rect[2]
    if angle < -45:
        angle += 90
        rotated = True

    center = (int((x1+x2)/2), int((y1+y2)/2))
    size = (int(mult*(x2-x1)),int(mult*(y2-y1)))

    M = cv.getRotationMatrix2D((size[0]/2, size[1]/2), angle, 1.0)
    cropped_W = W if not rotated else H
    cropped_H = H if not rotated else W

    cropped_mask = cv.getRectSubPix(filtered_mask, size, center)
    cropped_mask = cv.warpAffine(cropped_mask, M, size)
    cropped_Rotated_mask = cv.getRectSubPix(cropped_mask, (int(cropped_W*mult), int(cropped_H*mult)), (size[0]/2, size[1]/2))

    cropped_img = cv.getRectSubPix(img, size, center)
    cropped_img = cv.warpAffine(cropped_img, M, size)
    cropped_Rotated_img = cv.getRectSubPix(cropped_img, (int(cropped_W*mult), int(cropped_H*mult)), (size[0]/2, size[1]/2))

    height = cropped_Rotated_mask.shape[0]
    width = cropped_Rotated_mask.shape[1]
    return cropped_Rotated_mask, cropped_Rotated_img, height, width

def flip_image(cropped_Rotated_mask, cropped_Rotated_img, height, width):
    hsv = cv.cvtColor(cropped_Rotated_mask, cv.COLOR_BGR2HSV)
    mask = cv.inRange(hsv, lower, upper)
    M = cv.moments(mask)
    cx = int(M['m10'] / M['m00'])
    cy = int(M['m01'] / M['m00'])

    # Calculate the angle of rotation required
    angle = np.arctan2(cy - mask.shape[0] / 2, cx - mask.shape[1] / 2) * 180 / np.pi
    # Calculate the closest 90-degree angle to the calculated angle
    rounded_angle = 90 * round(angle / 90)

    # Rotate the image
    rows, cols = mask.shape[:2]
    M = cv.getRotationMatrix2D((cols / 2, rows / 2), rounded_angle, 1)
    cropped_Rotated_mask = cv.warpAffine(cropped_Rotated_mask, M, (cols, rows))
    cropped_Rotated_img = cv.warpAffine(cropped_Rotated_img, M, (cols, rows))

    height = cropped_Rotated_mask.shape[0]
    width = cropped_Rotated_mask.shape[1]

    if height > width:
        cropped_Rotated_img = cv.rotate(cropped_Rotated_img, cv.ROTATE_90_COUNTERCLOCKWISE)
        cropped_Rotated_mask = cv.rotate(cropped_Rotated_mask, cv.ROTATE_90_COUNTERCLOCKWISE)
    return cropped_Rotated_mask, cropped_Rotated_img, height, width

def output_and_log_processing_errors(BASE_DIR, name, height, width, cutoff_size, img1, cropped_Rotated_img, cropped_Rotated_mask):
    if (height * width) > cutoff_size:

        try:
            # Create directory for this error case
            error_dir = BASE_DIR / "processing_errors" / "crop_rotate_size" / name
            error_dir.mkdir()

            # Write files to error directory
            cv.imwrite(str(error_dir / f"{name}_mask.png"), cropped_Rotated_mask)
            cv.imwrite(str(error_dir / f"{name}_original.png"), img1)

            # Write to log file
            log_file = BASE_DIR / "logs" / "processing_error_logs.txt"
            with open(log_file, 'a') as f:
                f.write(f'\n{name} was too large, post-processing. Please check file\n')

        except FileExistsError:
            print(f"Error folder for {name} already exists")
            log_file = BASE_DIR / "logs" / "processing_error_logs.txt"
            with open(log_file, 'a') as f:
                f.write(f'\n{name} was processed as an error previously. Please check file.\n')


    else:
        try:
            # Create directory for this specific fingerprint
            fingerprint_dir = BASE_DIR / "fingerprints" / name
            fingerprint_dir.mkdir()

            # Write files with naming convention to new folder
            cv.imwrite(str(fingerprint_dir / f"{name}_mask.png"), cropped_Rotated_mask)
            cv.imwrite(str(fingerprint_dir / f"{name}_img.png"), cropped_Rotated_img)

        except FileExistsError:
            print(f"Folder for {name} already exists")
            log_file = BASE_DIR / "logs" / "processing_error_logs.txt"
            with open(log_file, 'a') as f:
                f.write(f'\n{name} was processed as a duplicate. Please check file. \n')

    return
########################################################################################################################


########################################################################################################################
# the main workhorse of this script, combines the processes above and handles generic errors that crop up.
def process_image(image_info):
    i, BASE_DIR, directory, image_name, lower, upper, kernel_size, threshold_value, min_area, num_patches, mult, cutoff_size = image_info
    # progress info
    print("Progress: {0}/{1}".format(i + 1, len(images_list)))

    img, name = read_image(BASE_DIR, directory, image_name)
    img = correct_image_rotation(img)
    mask, blurred_regions = apply_thresholds(img, lower, upper, kernel_size)
    contours = find_contours(blurred_regions, threshold_value)
    try:
        conts, filtered_mask = filter_contours(img, mask, contours, min_area, num_patches)
        rect, box = find_minimum_rotated_bounding_box(conts)
        cropped_Rotated_mask, cropped_Rotated_img, height, width = crop_and_rotate_image(filtered_mask, img, rect, box, mult)
        cropped_Rotated_mask, cropped_Rotated_img, height, width = flip_image(cropped_Rotated_mask, cropped_Rotated_img, height, width)
        output_and_log_processing_errors(BASE_DIR, name, height, width, cutoff_size, img, cropped_Rotated_img, cropped_Rotated_mask)
    except Exception as e:
        error_dir = BASE_DIR / "processing_errors" / "crop_rotate_generic" / name
        error_dir.mkdir()

        cv.imwrite(str(error_dir / f"{name}.png"), img)

        print(f"An unknown error occurred while cropping/rotating {name}")
        log_file = BASE_DIR / "logs" / "processing_error_logs.txt"
        with open(log_file, 'a') as f:
            f.write(
                '\n{0}. An unknown error occurred while cropping/rotating. Error message: {1} \n'.format(name, str(e)))
    return
########################################################################################################################


if __name__ == '__main__':
    # a clunky way to record processing times
    start_time = datetime.datetime.now()

    #pre-empt error logging
    error_log_file = BASE_DIR / "logs" / "processing_error_logs.txt"
    with open(error_log_file, 'a') as f:
        f.write(
            '\n{0} - Cropping and rotating images \n'.format(datetime.datetime.now()))


########################################################################################################################
    # parallel processing the above function to speed things along. i should probably wrap this in a function
    # create a list of tuples with the image information
    image_info_list = [
        (i, BASE_DIR, directory, image_name, lower, upper, kernel_size, threshold_value, min_area, num_patches, mult, cutoff_size)
        for i, image_name in enumerate(images_list)]
    # create a multiprocessing pool with the number of available CPU cores
    pool = multiprocessing.Pool()
    # map the list of image information tuples to the process_image function
    pool.map(process_image, image_info_list)
    # close the pool and wait for the work to finish
    pool.close()
    pool.join()
########################################################################################################################

    # still a clunky way to record processing times, but effective
    processing_time = datetime.datetime.now() - start_time
    # print the time taken to process all images
    print("Time taken: ", processing_time)

    timing_log_file = BASE_DIR / "logs" / "processing_times.txt"
    with open(timing_log_file, 'a') as f:
        f.write('\n Crop and rotate - {0} files processed in {1} minutes. {2} \n'.format(
            str(len(images_list) + 1), str(processing_time), date.today()))
