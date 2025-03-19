import os
import pandas as pd
from pathlib import Path
import csv
import datetime
from datetime import date
import sys


########################################################################################################################
########################################## GUI-DEFINED PATHS AND VALUES ################################################
BASE_DIR = Path(sys.argv[1])
focal_file = sys.argv[2]
test_file = sys.argv[3]
filter_by_sex = sys.argv[4].lower() == 'true'
filter_by_size = sys.argv[5].lower() == 'true'
date_filter = sys.argv[6]
# Define the target subdirectory (should only be fingerprints)
directory = BASE_DIR / "fingerprints"
# Load user-set parameters for fingerprint extraction
df = pd.read_csv(os.path.join(BASE_DIR, "data/user_parameters.csv"))
# Convert to dictionary (keys = parameters, values = converted numbers)
params = {row["Parameter"]: float(row["Value"]) for _, row in df.iterrows()}
# variable defining how much uncertainty in individual size i will accept for comparisons.
size_offset = float(params["size_offset"])
########################################################################################################################

focal_file_path = BASE_DIR / "data" / focal_file
test_file_path = BASE_DIR / "data" / test_file
# read in context for each image
focal_df = pd.read_csv(str(focal_file_path)) # a csv containing "focal","size","datef","sex","id"
query_df = pd.read_csv(str(test_file_path)) # "focal","size","datef","sex","id"

images_list = os.listdir(str(directory))  # List and print all files in directory.

def get_list_focal_examples(images_list):
    # initialize list to accept photo examples of focal individual
    list_focal_examples = []
    list_focal = focal_df.iloc[:, 0] # split off first column of within-week beetle names as list

    # for every unique within-week name, find all photo examples of that individual.
    # this requires images of format DATE_SOMENAME_FILENUMBER. Compares "DATE" and "SOMENAME" for matches
    for i in range(0,len(list_focal)):
        matching = [s for s in images_list if s.split("_")[0] == list_focal[i].split("_")[0] and s.split("_")[1] == list_focal[i].split("_")[1]]
        list_focal_examples.append(matching)

    return list_focal, list_focal_examples


def get_list_test(focal_df, query_df, size_offset, filter_by_sex, filter_by_size, date_filter):
    list_test = []

    for _, focal_row in focal_df.iterrows():
        conditions = []

        # Size filtering
        if filter_by_size:
            size_condition = ((query_df["size"].between(focal_row["size"] - size_offset,
                                                        focal_row["size"] + size_offset)) |
                              pd.isnull(focal_row["size"]) |
                              pd.isnull(query_df["size"]))
            conditions.append(size_condition)

        # Date filtering
        if date_filter == "before":
            conditions.append(query_df["datef"] < focal_row["datef"])
        elif date_filter == "after":
            conditions.append(query_df["datef"] > focal_row["datef"])

        # Sex filtering
        if filter_by_sex:
            sex_condition = ((query_df["sex"] == focal_row["sex"]) |
                             pd.isnull(focal_row["sex"]) |
                             pd.isnull(query_df["sex"]))
            conditions.append(sex_condition)

        # Combine all conditions
        if conditions:
            combined_condition = conditions[0]
            for condition in conditions[1:]:
                combined_condition = combined_condition & condition
            refined = query_df[combined_condition]
        else:
            refined = query_df

        list_test.append(refined.iloc[:, 0])

    return list_test

def get_list_test_examples(list_test, images_list):
    list_test_examples = []
    # for every unique within-week name of potential matches to focal, find all photo examples of those individuals.
    for sublist in list_test:
        sublist = sublist.tolist()
        temp = []
        for i in sublist:
            matching = [s for s in images_list if str(i) in s]
            temp.append(matching)
        flat_list = [item for sublist in temp for item in sublist]
        list_test_examples.append(flat_list)

        for i in range(len(list_test_examples)):
            if not list_test_examples[i]:
                list_test_examples[i] = ["No matching"]

    return list_test_examples

def generate_lists(images_list, focal_df, query_df, size_offset, filter_by_sex, filter_by_size, date_filter):
    list_focal, list_focal_examples = get_list_focal_examples(images_list)
    list_test = get_list_test(focal_df, query_df, size_offset, filter_by_sex, filter_by_size, date_filter)
    list_test_examples = get_list_test_examples(list_test, images_list)

    return list_focal_examples, list_test_examples


def product_of_matches(nested_list_1, nested_list_2, i):
    for item_1 in nested_list_1[i]:
        for item_2 in nested_list_2[i]:
            pairs.append([item_1, item_2])
    return

if __name__ == '__main__':
    start_time = datetime.datetime.now()
    print("Generating pairwise list - this may take some time!")
    list_focal_examples, list_test_examples = generate_lists(images_list, focal_df, query_df, size_offset, filter_by_sex, filter_by_size, date_filter)

    pairs = [['focal_image', 'test_image']]
    for i in range(len(list_focal_examples)):
        product_of_matches(list_focal_examples, list_test_examples, i)

    # Convert pairs list to DataFrame
    df_pairs = pd.DataFrame(pairs[1:], columns=['focal_image', 'test_image'])

    # Extract focal name and test name (first two elements of filename)
    df_pairs['focal_name'] = df_pairs['focal_image'].apply(lambda x: "_".join(x.split("_")[:2]))
    df_pairs['test_name'] = df_pairs['test_image'].apply(lambda x: "_".join(x.split("_")[:2]))

    # Merge to add size and sex information
    df_pairs = df_pairs.merge(focal_df[['focal', 'size', 'sex']], left_on='focal_name', right_on='focal', how='left')
    df_pairs = df_pairs.rename(columns={'size': 'focal_size', 'sex': 'focal_sex'}).drop(columns=['focal'])

    df_pairs = df_pairs.merge(query_df[['focal', 'size', 'sex']], left_on='test_name', right_on='focal', how='left')
    df_pairs = df_pairs.rename(columns={'size': 'test_size', 'sex': 'test_sex'}).drop(columns=['focal'])

    # Save the updated DataFrame
    output_file = BASE_DIR / "data" / f"pairwise_comparison_list_{date.today()}.csv"
    df_pairs.to_csv(output_file, index=False)

    processing_time = datetime.datetime.now() - start_time
    # print the time taken to process all images
    print("Time taken: ", processing_time)

    timing_log_file = BASE_DIR / "logs" / "processing_times.txt"
    with open(timing_log_file, 'a') as f:
        f.write(f'\n Generating pairwise comparisons - {str(len(pairs) - 1)} matches processed in {str(processing_time)} minutes. {date.today()} \n')