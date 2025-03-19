from shiny import ui, render, reactive
import multiprocessing
from pathlib import Path
import subprocess
import sys

def check_surf_available():
    """Check if SURF feature detector is available"""
    try:
        import cv2
        surf = cv2.xfeatures2d.SURF_create()
        return True
    except (ImportError, AttributeError):
        return False


def process_starting_page_ui():
    # Check SURF availability at UI creation time
    surf_available = check_surf_available()

    # Create the fingerprint and comparison options dictionaries
    fingerprint_options = {
        "akaze_fingerprint": "AKAZE",
        "orb_fingerprint": "ORB",
        "sift_fingerprint": "SIFT"
    }
    comparison_options = {
        "akaze_compare": "AKAZE",
        "orb_compare": "ORB",
        "sift_compare": "SIFT",
    }

    if surf_available:
        fingerprint_options["surf_fingerprint"] = "SURF"
        comparison_options["surf_compare"] = "SURF"



    return ui.nav_panel(
        "Batch Processing",
        ui.card(
            ui.h3("Crop and rotate"),
            ui.div(
                ui.input_select(
                    "batch_crop_rotate_directory",
                    "Photos to crop and rotate are located in:",
                    choices={"unprocessed_photos": "Unprocessed Photos Directory", "temp": "Temporary Directory"},
                    width="35%"
                ),
                class_="mb-3"
            ),
            ui.div(
                ui.input_action_button(
                    "start_batch_crop_rotate_process",
                    "Start Image Cropping and Rotating",
                    class_="btn-primary",
                    width="35%"
                ),
                class_="d-flex justify-content-end"
            )
        ),
        ui.card(
            ui.h3("Extract Fingerprints"),
            ui.row(
                ui.column(6,
                    ui.input_select(
                        "fingerprint_extraction_directory",
                        "Photos to extract fingerprints from are located in:",
                        choices={"fingerprints": "Fingerprints Directory", "temp": "Temporary Directory"},
                        width="70%"
                    ),
                          class_="mb-3"
                          ),
                ui.column(6,
                          ui.h4("Choose types of fingerprints to extract:"),
                          ui.input_checkbox_group(
                              "detectors",
                              " ",
                              fingerprint_options,
                              selected=["akaze_fingerprint", "orb_fingerprint", "sift_fingerprint"]
                          ),
                          )
            ),
            ui.div(
                ui.input_action_button(
                    "start_fingerprint_extraction_process",
                    "Start Fingerprint Extraction",
                    class_="btn-primary",
                    width="35%"
                ),
                class_="d-flex justify-content-end"
            )
        ),
        ui.card(
            ui.h3("Generate Pairwise List"),
            ui.row(
                ui.column(6,
                   ui.div(
                       ui.input_file("focal_csv", "Choose focal CSV file", accept=[".csv"], width="70%"),
                    class_="mb-3"
                   ),
                      ui.div(
                          ui.input_file("test_csv", "Choose query CSV file", accept=[".csv"], width="70%"),
                          class_="mb-3"
                      ),
                      ),
                ui.column(6,
                          ui.h4("Filtering Options:"),
                          ui.div(
                              ui.input_checkbox("filter_by_sex", "Filter by sex", value=True),
                              ui.input_checkbox("filter_by_size", "Filter by size", value=True),
                              class_="mb-3"
                          ),
                   ui.div(
                       ui.input_select(
                           "date_filter",
                           "Date filtering:",
                           choices={
                               "before": "Test against previous photos (recaptures)",
                               "after": "Test against subsequent photos (future captures)",
                               "all": "No date filtering - not recommended"
                           },
                           selected="before",
                           width = "50%"
                       ),
                       class_="mb-3"
                   )
                   ),
            ),
            ui.div(
                ui.input_action_button(
                    "start_pairwise_list_process",
                    "Generate list of potential matches",
                    class_="btn-primary",
                    width="35%"
                ),
                class_="d-flex justify-content-end"
            )
        ),
        ui.card(
            ui.h3("Run Pairwise Comparisons"),
            ui.row(
                ui.column(6,
                          ui.div(
                              ui.input_file("pairwise_csv", "Choose pairwise CSV file", accept=[".csv"], width="70%"),
                              class_="mb-3"
                          )
                          ),
                ui.column(6,
                          ui.h4("Choose types of comparison to run:"),
                          ui.input_checkbox_group(
                              "comparisons",
                              " ",
                              comparison_options,
                              selected=["akaze_compare", "orb_compare", "sift_compare"]
                          )
                          )
            ),
            ui.div(
                ui.input_action_button(
                    "start_pairwise_comparisons_process",
                    "Start fingerprint comparisons",
                    class_="btn-primary",
                    width="35%"
                ),
                class_="d-flex justify-content-end"
            )
        ),
        ui.tags.hr({"style": "border-top: 3px solid #5c5c5c; margin-top: 30px; margin-bottom: 30px;"}),
        ui.card(
            {"style": "border: 2px solid #4682B4; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);"},
            ui.card_header({"style": "background-color: #4682B4; color: white;"},
                           "Run Within-Individual Quality Check"),
            ui.card_body(
                ui.h4("Choose types of comparison to run:"),
                ui.input_checkbox_group(
                    "self_comparisons",
                    " ",
                    comparison_options,
                    selected=["akaze_compare", "orb_compare", "sift_compare"]
                ),
                ui.div(
                    ui.input_action_button(
                        "start_self_comparisons_process",
                        "Start within-individual quality check",
                        class_="btn-primary",
                        width="35%"
                    ),
                    class_="d-flex justify-content-end"
                )
            )
        )
    )


def run_process(script_name, *args):
    """Generic function to run a subprocess"""
    try:
        cmd = [sys.executable, str(script_name)] + [str(arg) for arg in args]

        popen_kwargs = {
            'stdout': None,
            'stderr': None,
            'shell': False,
        }

        if sys.platform == 'win32':
            popen_kwargs['creationflags'] = (
                subprocess.CREATE_NEW_PROCESS_GROUP |
                subprocess.DETACHED_PROCESS
            )
        else:
            popen_kwargs['start_new_session'] = True

        process = subprocess.Popen(cmd, **popen_kwargs)
        return process

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise

def process_starting_page_server(input, output, session, BASE_DIR):
    # Reactive values to track different processes
    is_processing = reactive.value(False)

    def disable_all_buttons():
        """Helper function to disable all action buttons"""
        ui.update_action_button("start_batch_crop_rotate_process", disabled=True)
        ui.update_action_button("start_fingerprint_extraction_process", disabled=True)
        ui.update_action_button("start_pairwise_list_process", disabled=True)
        ui.update_action_button("start_pairwise_comparisons_process", disabled=True)
        ui.update_action_button("start_self_comparisons_process", disabled=True)

    def enable_all_buttons():
        """Helper function to disable all action buttons"""
        ui.update_action_button("start_batch_crop_rotate_process", disabled=False)
        ui.update_action_button("start_fingerprint_extraction_process", disabled=False)
        ui.update_action_button("start_pairwise_list_process", disabled=False)
        ui.update_action_button("start_pairwise_comparisons_process", disabled=False)
        ui.update_action_button("start_self_comparisons_process", disabled=False)

    @reactive.Effect
    @reactive.event(input.start_batch_crop_rotate_process)
    def _():
        if not is_processing():
            is_processing.set(True)
            disable_all_buttons()
            try:
                p = run_process(
                    "batch_segment_crop_rotate_subprocess.py",
                    BASE_DIR,
                    input.batch_crop_rotate_directory()
                )
                is_processing.set(False)
            except Exception as e:
                print(f"Failed to start crop/rotate process: {e}")
                enable_all_buttons()
                is_processing.set(False)

    @reactive.Effect
    @reactive.event(input.start_fingerprint_extraction_process)
    def _():
        if not is_processing():
            is_processing.set(True)
            disable_all_buttons()
            try:
                p = run_process(
                    "batch_store_values_subprocess.py",
                    BASE_DIR,
                    input.fingerprint_extraction_directory(),
                    *input.detectors()
                )
                is_processing.set(False)
            except Exception as e:
                print(f"Failed to start fingerprint extraction: {e}")
                enable_all_buttons()
                is_processing.set(False)

    @reactive.Effect
    @reactive.event(input.start_pairwise_list_process)
    def _():
        if not is_processing():
            is_processing.set(True)
            disable_all_buttons()
            try:
                p = run_process(
                    "generating_pairwise_lists_subprocess.py",
                    BASE_DIR,
                    input.focal_csv()[0]["name"],
                    input.test_csv()[0]["name"],
                    str(input.filter_by_sex()),
                    str(input.filter_by_size()),
                    input.date_filter()
                )
                is_processing.set(False)
            except Exception as e:
                print(f"Failed to start pairwise list generation: {e}")
                enable_all_buttons()
                is_processing.set(False)

    @reactive.Effect
    @reactive.event(input.start_pairwise_comparisons_process)
    def _():
        if not is_processing():
            is_processing.set(True)
            disable_all_buttons()
            try:
                p = run_process(
                    "parallel_crossmatching_subprocess.py",
                    BASE_DIR,
                    input.pairwise_csv()[0]["name"],
                    *input.comparisons()
                )
                is_processing.set(False)
            except Exception as e:
                print(f"Failed to start comparisons: {e}")
                enable_all_buttons()
                is_processing.set(False)

    @reactive.Effect
    @reactive.event(input.start_self_comparisons_process)
    def _():
        if not is_processing():
            is_processing.set(True)
            disable_all_buttons()
            try:
                p = run_process(
                    "within_individual_assessment_subprocess.py",
                    BASE_DIR,
                    *input.comparisons()
                )
                is_processing.set(False)
            except Exception as e:
                print(f"Failed to start within-individual comparisons: {e}")
                enable_all_buttons()
                is_processing.set(False)

