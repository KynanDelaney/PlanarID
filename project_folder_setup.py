import csv
from pathlib import Path
from datetime import date


# Define base project location - Documents, Images, wherever
BASE_DIR = Path.home() / "Documents"
# Choose a name for this project
project = "TEST"



# Set up project directory
project_directory = BASE_DIR / project

def create_directory(directory):
    try:
        directory.mkdir(parents=True, exist_ok=False)
        print(f"{directory.name} folder was created")
    except FileExistsError:
        print(f"{directory.name} folder already exists")

def create_log_file(log_path, log_description):
    try:
        with open(log_path, 'x') as f:
            f.write(f'{log_description} {project} database. \nCreated {date.today()} \n')
    except FileExistsError:
        print(f"The '{log_description}' file already exists")


# Create necessary directories
directories = [
    project_directory/'unprocessed_photos',
    project_directory/'processing_errors',
    project_directory/'processing_errors'/'crop_rotate_generic',
    project_directory/'processing_errors'/'crop_rotate_size',
    project_directory/'processing_errors'/'fingerprinting',
    project_directory/'fingerprints',
    project_directory/'logs',
    project_directory/'temp',
    project_directory/'data',
    project_directory/'scripts'
]

for directory in directories:
    create_directory(directory)

# Create log files
log_paths = [
    project_directory/'logs/processing_error_logs.txt',
    project_directory/'logs/fingerprinting_error_logs.txt',
    project_directory/'logs/cross-matching_error_logs.txt',
    project_directory/'logs/processing_times.txt'
]

log_descriptions = [
    'Initial image processing errors log file for',
    'Fingerprinting errors log file for',
    'Pairwise comparison errors log file for',
    'Processing times log file for'
]

for log_path, log_description in zip(log_paths, log_descriptions):
    create_log_file(log_path, log_description)


def create_user_parameters_csv(csv_path):
    parameters = [
        ("hue_low", 0.0),
        ("saturation_low", 0.0),
        ("value_low", 0.0),
        ("hue_high", 179.0),
        ("saturation_high", 255.0),
        ("value_high", 255.0),
        ("kernel_size", 11.0),
        ("threshold_value", 50.0),
        ("num_patches", 4.0),
        ("min_area", 7500.0),
        ("mult", 1.1),
        ("hessian_threshold", 500.0),
        ("n_features", 1000.0),
        ("akaze_threshold", 0.001),
        ("cutoff_size", 10000000.0),
        ("size_offset", 100.0),
        ("number_comparisons_considered", 20)
    ]

    try:
        with open(csv_path, 'x', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Parameter", "Value"])
            writer.writerows(parameters)
            print(f"CSV file '{csv_path.name}' was created successfully.")
    except FileExistsError:
        print(f"CSV file '{csv_path.name}' already exists.")


# Define the CSV file path
user_parameters_path = project_directory / 'data' / 'user_parameters.csv'

# Create the CSV file
create_user_parameters_csv(user_parameters_path)

def create_data_recording_template(csv_path):
    try:
        with open(csv_path, 'x', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["focal", "datef", "sex", "size"])
            print(f"CSV file '{csv_path.name}' was created successfully.")
    except FileExistsError:
        print(f"CSV file '{csv_path.name}' already exists.")

# Define the CSV file path
focal_df_template_path = project_directory / 'data' / 'focal_df_template.csv'

# Create the CSV file
create_data_recording_template(focal_df_template_path)