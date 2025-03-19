import cv2 as cv
import datetime
import sys
import csv
from datetime import date
import numpy as np
from pathlib import Path
import pandas as pd
import multiprocessing
import os

########################################################################################################################
########################################## GUI-DEFINED PATHS AND VALUES ################################################
BASE_DIR = Path(sys.argv[1])
df_path = sys.argv[2]
comparison_types = sys.argv[3:]  # All remaining arguments are types of comparison to run
# Define the target subdirectory (should only be fingerprints)
directory = "fingerprints"

# Load user-set parameters for fingerprint extraction
df = pd.read_csv(os.path.join(BASE_DIR, "data/user_parameters.csv"))
# Convert to dictionary (keys = parameters, values = converted numbers)
params = {row["Parameter"]: float(row["Value"]) for _, row in df.iterrows()}

# variable defining how much uncertainty in individual size i will accept for comparisons.
filtered_n = float(params["number_comparisons_considered"])
########################################################################################################################


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

            des1_path = BASE_DIR / directory / a / f"{a}_{comp_info['suffix']}_mask.txt"
            des2_path = BASE_DIR / directory / b / f"{b}_{comp_info['suffix']}_mask.txt"
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
    for row in chunk.itertuples(index=False):
        compare(row.focal_image, row.test_image, results_dict)

def filter_lowest_n(group, n=filtered_n):
    result = pd.DataFrame()
    value_columns = [col for col in group.columns if col.endswith('_values')]

    for col in value_columns:
        # Convert *_values columns to numeric, coercing errors to NaN
        group[col] = pd.to_numeric(group[col], errors='coerce')

        # Sort by the current *_values column and take the top N
        top_n = group.nsmallest(n, col)

        # Ensure focal_name is part of the result
        top_n['focal_name'] = group['focal_name'].iloc[0]  # Add focal_name back

        result = pd.concat([result, top_n])

    return result.drop_duplicates()

if __name__ == '__main__':
    # Read in the dataframe, ensuring sex columns are read as strings
    pairwise_list_file = BASE_DIR / "data" / df_path
    df = pd.read_csv(str(pairwise_list_file), dtype={'focal_sex': str, 'test_sex': str})
    print(df.head())

    # Get the number of rows
    N = len(df)

    # Print the statement
    print(f"Running {N} pairwise comparisons - this may take some time!")

    log_file = BASE_DIR / "logs" / "crossmatching_error_logs.txt"
    with open(log_file, 'a') as f:
        f.write(f'\n{datetime.datetime.now()} - Performing pairwise comparisons for: {", ".join(comparison_types)} \n')

    start_time = datetime.datetime.now()

    # Define the chunk size - subsets of data to work on to avoid RAM issues
    chunk_size = 100000

    # Split the dataframe into chunks
    chunks = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]

    # Set up the multiprocessing pool
    with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
        manager = multiprocessing.Manager()
        results_dict = manager.dict()

        # Map the compare_wrapper function to each chunk of the dataframe
        results = [pool.apply_async(compare_wrapper, args=(chunk, results_dict)) for chunk in chunks]

        # Wait for all processes to finish
        for result in results:
            result.get()

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
        row = {
            'focal_image': focal,
            'test_image': test,
            **values  # Unpack all values
        }
        results_list.append(row)

    results_df = pd.DataFrame(results_list)

    # Merge results back to the original dataframe
    final_df = pd.merge(df, results_df, on=['focal_image', 'test_image'], how='left')
    final_df['flag'] = 'unprocessed'

    # Export the new dataframe as a CSV
    output_file = BASE_DIR / 'data' / f'comparison_results_{date.today()}.csv'
    final_df.to_csv(output_file, index=False) # R may load sex columns poorly


    # Group by 'focal_name' and apply the filtering function
    filtered_df = final_df.groupby('focal_name', group_keys=True).apply(filter_lowest_n)

    # Export the filtered DataFrame to a CSV
    filtered_output_file = BASE_DIR / 'data' / f'filtered_comparison_results_{date.today()}.csv'
    filtered_df.to_csv(filtered_output_file, index=False)

    processing_time = datetime.datetime.now() - start_time
    print("Time taken: ", processing_time)

    timing_log_file = BASE_DIR / "logs" / "processing_times.txt"
    with open(timing_log_file, 'a') as f:
        f.write(
            f'\n Pairwise comparisons - {len(df)} matches processed for {", ".join(comparison_types)} in {processing_time} minutes. {date.today()} \n')
