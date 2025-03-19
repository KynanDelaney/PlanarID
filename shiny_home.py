from shiny import App, ui
from pathlib import Path
from image_processing_page import image_processing_page_ui, image_processing_page_server
from individual_matching_page import individual_matching_page_ui, individual_matching_page_server
from details_page import details_page_ui, details_page_server
from within_individual_comparison_page import within_individual_comparison_page_ui, within_individual_comparison_page_server
from example_matching_page import example_matching_page_ui, example_matching_page_server
from process_starting_page import process_starting_page_ui, process_starting_page_server


# Define the base path for images
BASE_DIR = Path.home() /"Documents"/"TEST"



app_ui = ui.page_navbar(
    details_page_ui(),
    image_processing_page_ui(BASE_DIR),
    example_matching_page_ui(),
    process_starting_page_ui(),
    individual_matching_page_ui(),
    within_individual_comparison_page_ui(),
    ui.nav_spacer(),
    ui.nav_control(ui.input_dark_mode()),
    title="PlanarID",
)

def server(input, output, session):
    details_page_server(input, output, session, BASE_DIR)
    image_processing_page_server(input, output, session, BASE_DIR)
    example_matching_page_server(input, output, session, BASE_DIR)
    process_starting_page_server(input, output, session, BASE_DIR)
    individual_matching_page_server(input, output, session, BASE_DIR)
    within_individual_comparison_page_server(input, output, session)


app = App(app_ui, server, static_assets=BASE_DIR)
