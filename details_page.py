from shiny import ui, render
import pandas as pd
import os

def details_page_ui():
    return ui.nav_panel("Project Details",
        ui.card(
            ui.h3("Active Parameters"),
            ui.output_data_frame("params_table")
        ),
        ui.card(
            ui.h3("Directory Details"),
            ui.output_ui("dir_details"),
            class_="p-0"
        ),
        ui.card(
            ui.h3("Potential Pairwise Comparisons"),
            ui.output_ui("pairwise_details"),
            class_="p-0"
        )
    )


def details_page_server(input, output, session, BASE_DIR):
    @output
    @render.data_frame
    def params_table():
        try:
            df = pd.read_csv(os.path.join(BASE_DIR, "data/user_parameters.csv"))
            return render.DataGrid(df)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            return render.DataGrid(pd.DataFrame({'Message': ['No parameters saved yet']}))

    @output
    @render.ui
    def dir_details():
        def count_folders(directory):
            # Function used to count fingerprints (many files grouped in meaningful folders)
            full_path = os.path.join(BASE_DIR, directory)
            try:
                return len([item for item in os.listdir(full_path)
                            if os.path.isdir(os.path.join(full_path, item))])
            except (FileNotFoundError, NotADirectoryError):
                return 0

        def count_files(directory):
            # Function used to count unprocessed photos, generally, or items in temp folder
            full_path = os.path.join(BASE_DIR, directory)
            try:
                return len([item for item in os.listdir(full_path)
                            if os.path.isfile(os.path.join(full_path, item))])
            except (FileNotFoundError, NotADirectoryError):
                return 0

        def count_error_subfolders(subfolder):
            full_path = os.path.join(BASE_DIR, "processing_errors", subfolder)
            try:
                return len([item for item in os.listdir(full_path)
                            if os.path.isdir(os.path.join(full_path, item))])
            except (FileNotFoundError, NotADirectoryError):
                return 0

        unprocessed = count_files("unprocessed_photos")
        fingerprints = count_folders("fingerprints")
        temps = count_files("temp")

        # Count subfolders within error directories
        crop_rotate_size_errors = count_error_subfolders("crop_rotate_size")
        crop_rotate_generic_errors = count_error_subfolders("crop_rotate_generic")
        fingerprinting_errors = count_error_subfolders("fingerprinting")

        return ui.tags.div(
            ui.tags.table(
                ui.tags.thead(
                    ui.tags.tr(
                        ui.tags.th("Directory", style="font-weight: bold;"),
                        ui.tags.th("Count")
                    )
                ),
                ui.tags.tbody(
                    ui.tags.tr(
                        ui.tags.td("Unprocessed Photos (files)"),
                        ui.tags.td(str(unprocessed))
                    ),
                    ui.tags.tr(
                        ui.tags.td("Processed Photos (folders)"),
                        ui.tags.td(str(fingerprints))
                    ),
                    ui.tags.tr(
                        ui.tags.td("Processing Errors:"),
                        ui.tags.td("")  # Empty cell for formatting
                    ),
                    ui.tags.tr(
                        ui.tags.td("→ Crop/Rotate Size Errors (folders)", style="padding-left: 20px;"),
                        ui.tags.td(str(crop_rotate_size_errors))
                    ),
                    ui.tags.tr(
                        ui.tags.td("→ Crop/Rotate Generic Errors (folders)", style="padding-left: 20px;"),
                        ui.tags.td(str(crop_rotate_generic_errors))
                    ),
                    ui.tags.tr(
                        ui.tags.td("→ Fingerprinting Errors (folders)", style="padding-left: 20px;"),
                        ui.tags.td(str(fingerprinting_errors))
                    ),
                    ui.tags.tr(
                        ui.tags.td("Temporary items (files)"),
                        ui.tags.td(str(temps))
                    )
                ),
                style="width: 100%; border-collapse: collapse; margin-top: 20px;",
                _add_class="table table-striped"
            ),
            style="width: 100%",  # Add width to the div as well
        )

    @output
    @render.ui
    def pairwise_details():
        def count_fingerprints(directory):
            full_path = os.path.join(BASE_DIR, directory)
            try:
                return len([item for item in os.listdir(full_path)
                            if os.path.isdir(os.path.join(full_path, item))])
            except (FileNotFoundError, NotADirectoryError):
                return 0

        def evaluate_pairwise():
            num_fingerprints = count_fingerprints("fingerprints")
            if num_fingerprints != 0:
                pairwise_comparisons = (num_fingerprints * (num_fingerprints - 1)) // 2
            else:
                pairwise_comparisons = 0
            return pairwise_comparisons

        pairwise_comparisons = evaluate_pairwise()

        return ui.tags.div(
            ui.tags.table(
                ui.tags.thead(
                    ui.tags.tr(
                        ui.tags.th("Comparison Type"),
                        ui.tags.th("Count")
                    )
                ),
                ui.tags.tbody(
                    ui.tags.tr(
                        ui.tags.td("Naive Assessment"),
                        ui.tags.td(f"{pairwise_comparisons:,}") #nice number format
                    )
                ),
                style = "width: 100%; border-collapse: collapse; margin-top: 20px;",
                _add_class = "table table-striped"
            ),
            style="width: 100%",  # Add width to the div as well
        )