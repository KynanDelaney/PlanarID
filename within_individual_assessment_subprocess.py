import cv2 as cv
import datetime
import sys
import os
from datetime import date
import numpy as np
from pathlib import Path
import pandas as pd
import multiprocessing
from itertools import combinations


########################################################################################################################
########################################## GUI-DEFINED PATHS AND VALUES ################################################
BASE_DIR = Path(sys.argv[1])
# Define the target subdirectory (should only be fingerprints)
directory = BASE_DIR / "fingerprints"

# Define the initial list of comparison types
comparison_types = sys.argv[2:]  # All remaining arguments are types of comparison to run
########################################################################################################################


########################################################################################################################
########################################### MANUALLY DEFINE PATHS AND VALUES ###########################################
# Define base project directory
#BASE_DIR = Path.home() / "Documents/TEST"

# Define the target subdirectory (should only be fingerprints)
#directory = BASE_DIR/ "fingerprints"
# Choose which fingerprint comparisons to use, delete as appropriate. SURF may not be available on all devices.
#comparison_types = ['akaze_compare', 'orb_compare', 'sift_compare']

########################################################################################################################

#def check_surf_available():
#    """Check if SURF feature detector is available"""
#    try:
#        surf = cv.xfeatures2d.SURF_create()
#        return True
#    except (ImportError, AttributeError):
#        return False

# Add 'surf_compare' if SURF is available
#if check_surf_available():
#    comparison_types.append('surf_compare')

########################################################################################################################
def pairwise_surf(x, y):
    bf = cv.BFMatcher(cv.NORM_L2, crossCheck=True)
    matches_surf = bf.match(x, y)
    dist = [m.distance for m in matches_surf]
    values = sum(dist) / len(dist)
    return values
def pairwise_sift(x, y):
    bf = cv.BFMatcher(cv.NORM_L2, crossCheck=True)
    matches_sift = bf.match(x, y)
    dist = [m.distance for m in matches_sift]
    values = sum(dist) / len(dist)
    return values
def pairwise_orb(x, y):
    bf = cv.BFMatcher(cv.NORM_HAMMING, crossCheck=True)
    matches_orb = bf.match(x, y)
    dist = [m.distance for m in matches_orb]
    values = sum(dist) / len(dist)
    return values
def pairwise_akaze(x, y):
    bf = cv.BFMatcher(cv.NORM_HAMMING, crossCheck=True)
    matches_akaze = bf.match(x, y)
    dist = [m.distance for m in matches_akaze]
    values = sum(dist) / len(dist)
    return values
########################################################################################################################

def compare(a, b, results_dict):
    print(f"Comparing {a} vs {b}")

    # Dictionary mapping comparison types to their functions and descriptor files
    comparison_map = {
        'surf_compare': {
            'func': pairwise_surf,
            'suffix': 'surf',
            'dtype': 'float32',
            'norm': cv.NORM_L2
        },
        'sift_compare': {
            'func': pairwise_sift,
            'suffix': 'sift',
            'dtype': 'float32',
            'norm': cv.NORM_L2
        },
        'orb_compare': {
            'func': pairwise_orb,
            'suffix': 'orb',
            'dtype': 'uint8',
            'norm': cv.NORM_HAMMING
        },
        'akaze_compare': {
            'func': pairwise_akaze,
            'suffix': 'akaze',
            'dtype': 'uint8',
            'norm': cv.NORM_HAMMING
        }
    }

    results = {}

    # Process only the selected comparison types
    for comp_type in comparison_types:
        try:
            comp_info = comparison_map[comp_type]

            des1_path = directory / a / f"{a}_{comp_info['suffix']}_mask.txt"
            des2_path = directory / b / f"{b}_{comp_info['suffix']}_mask.txt"
            des1 = np.loadtxt(str(des1_path)).astype(comp_info['dtype'])
            des2 = np.loadtxt(str(des2_path)).astype(comp_info['dtype'])

            value = comp_info['func'](des1, des2)
            results[f"{comp_info['suffix']}_values"] = value

        except Exception as e:
            results[f"{comp_info['suffix']}_values"] = "NA"
            error_log_file = BASE_DIR / "logs" / "crossmatching_error_logs.txt"
            with open(error_log_file, 'a') as f:
                f.write(f'\nAn error occurred while comparing {a} vs {b} with {comp_info["suffix"]}: {str(e)} \n')

    results_dict[(a, b)] = results

def compare_wrapper(chunk, results_dict):
    for row in chunk[['focal_image', 'test_image']].itertuples(index=False):
        compare(row[0], row[1], results_dict)

def get_list_focal_examples(images_list):
    # Create a DataFrame from the list of filenames
    df = pd.DataFrame(images_list, columns=['focal_image'])

    # Extract the "[date]_[name]" part from each filename
    df['focal_name'] = df['focal_image'].apply(lambda x: "_".join(x.split("_")[:2]))

    # Group by the "[date]_[name]" part
    grouped = df.groupby('focal_name')['focal_image'].apply(list)

    # Convert grouped data to a list of lists
    list_focal_examples = grouped.tolist()

    return list_focal_examples

def pairwise_combinations(nested_list):
    for sublist in nested_list:
        for pair in combinations(sublist, 2):
            yield pair

# Function to extract focal name (first two elements)
def extract_name(image_id):
    parts = image_id.split("_")
    return "_".join(parts[:2])  # Retain only the first two elements

def store_output(df):
    output_file = BASE_DIR / 'data' / f'self_comparisons_{date.today()}.csv'
    try:
        df.to_csv(output_file, mode='x', index=False)
    except FileExistsError:
        print("Pairwise comparison file already exists. \nAppending new data to the existing file...")
        df.to_csv(output_file, mode='a', index=False)



if __name__ == '__main__':
    start_time = datetime.datetime.now()

    images_list = os.listdir(str(directory))  # List and print all files in directory.
    #print(images_list)

    list_focal_examples = get_list_focal_examples(images_list)
    combinations_generator = pairwise_combinations(list_focal_examples)
    combi = []
    # generate all pairwise comparisons
    for pair in combinations_generator:
        combi.append(pair)
    # Assess how many wasted comparisons are eliminated
    # print(len(combi))

    # Remove duplicates
    unique_pairs = set()
    for pair in combi:
        sorted_pair = tuple(sorted(set(pair)))
        unique_pairs.add(sorted_pair)

    df_unique_pairs = pd.DataFrame(list(unique_pairs), columns=['focal_image', 'test_image'])
    # Get the number of rows
    N = len(df_unique_pairs)

    # Print the statement
    print(f"Running {N} pairwise comparisons - this may take some time!")

    log_file = BASE_DIR / "logs" / "crossmatching_error_logs.txt"
    with open(log_file, 'a') as f:
        f.write('\n{0} - Performing self comparisons \n'.format(datetime.datetime.now()))


    # Define the chunk size - subsets of data to work on to avoid RAM issues
    chunk_size = 100000

    # Split the dataframe into chunks
    chunks = [df_unique_pairs[i:i + chunk_size] for i in range(0, len(df_unique_pairs), chunk_size)]

    # Set up the multiprocessing pool
    with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
        manager = multiprocessing.Manager()
        results_dict = manager.dict()

        # Map the compare_wrapper function to each chunk of the dataframe
        results = [pool.apply_async(compare_wrapper, args=(chunk, results_dict)) for chunk in chunks]

        # Wait for all processes to finish
        for result in results:
            result.get()  # Make sure to handle exceptions here if needed

    pool.close()
    pool.join()
    # Set up the multiprocessing pool
    #manager = multiprocessing.Manager()
    #results_dict = manager.dict()
    #pool = multiprocessing.Pool(multiprocessing.cpu_count())
    #print(multiprocessing.cpu_count())

    # Map the compare_wrapper function to each chunk of the dataframe
    #results = [pool.apply_async(compare_wrapper, args=(chunk, results_dict)) for chunk in chunks]

    # Wait for all processes to finish
    #for result in results:
    #    result.get()

    # Create a new dataframe with the results
    results_list = []
    for (focal, test), values in results_dict.items():
        row = {'focal_image': focal, 'test_image': test}
        row.update(values)
        results_list.append(row)

    new_df = pd.DataFrame(results_list)

    # Add new columns to the DataFrame
    #new_df["focal_image_path"] = new_df["focal_image"].apply(lambda x: f"fingerprints/{x}/{x}_img.png")
    #new_df["test_image_path"] = new_df["test_image"].apply(lambda x: f"fingerprints/{x}/{x}_img.png")
    new_df["focal_name"] = new_df["focal_image"].apply(extract_name)
    new_df["test_name"] = new_df["test_image"].apply(extract_name)

    store_output(new_df)


    processing_time = datetime.datetime.now() - start_time
    # print the time taken to process all images
    print("Time taken: ", processing_time)

    timing_log_file = BASE_DIR / "logs" / "processing_times.txt"
    with open(timing_log_file, 'a') as f:
        f.write(f'\n Self comparisons - {str(len(df_unique_pairs))} comparisons processed in {str(processing_time)} minutes. {date.today()} \n')