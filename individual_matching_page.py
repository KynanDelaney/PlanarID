from shiny import ui, render, reactive
import pandas as pd
import os
from datetime import datetime

# Constants
IMAGE_STYLE = """
    width: 60%;
    max-width: 60%;
    height: auto;
    max-height: 60vh;
    object-fit: contain;
    display: block;
    margin: 0 auto;
"""

BUTTON_STYLE = """
    margin: 5px;
    min-width: 120px;
"""

def individual_matching_page_ui():
    return ui.nav_panel("Individual Matching",
        ui.row(
            ui.column(6,
                ui.input_file("matches_upload", "Choose CSV file", accept=[".csv"],
                 width="80%")
            ),
            ui.column(3,
                ui.input_numeric("number_matches_considered", "Number of matches considered",
                                min=1, max=20, value=5)
            ),
            ui.column(3,
                ui.input_select("selected_algorithm", "Choice of algorithm:", choices=[])
            )
        ),
        ui.output_ui("main_interface")
    )

def individual_matching_page_server(input, output, session, BASE_DIR):
    # Reactive values
    current_data = reactive.value(None)  # Stores the current working dataset
    current_index = reactive.value(0)  # Current image index
    button_states = reactive.value({}) # Store the last known value for each button

    def load_data():
        if input.matches_upload() is not None:
            file_path = input.matches_upload()[0]["datapath"]
            df = pd.read_csv(file_path)
            return df
        return None


    def save_match(focal_name, test_name):
        """Save a match to the matches CSV file"""
        new_row = pd.DataFrame({
            'focal_name': [focal_name],
            'test_name': [test_name]
        })

        # Generate today's date in dd-mm-yyyy format
        date_stamp = datetime.now().strftime("%d-%m-%Y")

        # Append the date stamp to the filename
        MATCHES_CSV = os.path.join(BASE_DIR, f"data/matches_{date_stamp}.csv")

        # each day is treated as a new session. new matches will be appended or written to new files depending on current or new session.
        if os.path.exists(MATCHES_CSV):
            new_row.to_csv(MATCHES_CSV, mode='a', header=False, index=False)
        else:
            new_row.to_csv(MATCHES_CSV, mode='w', header=True, index=False)

    def process_uploaded_data(file_path, selected_algorithm, n_filter):
        """Process the uploaded CSV file and prepare the working dataset"""
        df = pd.read_csv(file_path, dtype={"flag": str}, quotechar='"', skipinitialspace=True)
        df.columns = df.columns.str.strip('"')

        # Filter out rows with processing notes
        df_filtered = df[df["flag"].fillna("").str.strip() == ""]

        # Sort by the selected algorithm's distance values
        df_filtered = df_filtered.sort_values(by=selected_algorithm)

        # Group by "focal_name" and aggregate relevant fields
        grouped = df_filtered.groupby("focal_name", group_keys=True).apply(
            lambda group: group.nsmallest(n_filter, selected_algorithm)
        ).reset_index(drop=True)

        # Aggregate the grouped data into lists
        final_grouped = grouped.groupby("focal_name").agg({
            "focal_image": "first",
            "test_image": lambda x: list(x),
            "test_name": lambda x: list(x),
            selected_algorithm: lambda x: list(x),
            "test_size": lambda x: list(x),
            "focal_size": "first",
            "flag": "first"
        }).reset_index()

        return final_grouped


    def get_test_images_length():
        """Get the number of test images for the current row"""
        if current_data() is None:
            return 0
        row = current_data().iloc[current_index()]
        return len(row["test_name"])


    def update_matches(focal_name, test_name=None):
        """Update the matches in the original CSV and current dataset"""
        if current_data() is None:
            return

        file_name = input.matches_upload()[0]["name"]  # Get file details

        if not file_name:
            print("Error: No original file path stored.")
            return

        file_path = os.path.join(BASE_DIR,"data/",file_name) # convert file details to known location in data folder

        df = pd.read_csv(file_path, dtype={"flag": str}, quotechar='"', skipinitialspace=True)

        #print("Before update:", df.head())  # Debugging check

        # Update flag for focal image
        mask = df["focal_name"] == focal_name
        df.loc[mask, "flag"] = "processed"

        if test_name:
            match_mask = (df["focal_name"] == focal_name) & (df["test_name"] == test_name)
            df.loc[match_mask, "flag"] = "match"
            save_match(focal_name, test_name)
        else:
            save_match(focal_name, focal_name)  # No match case

        #print("After update:", df.head())  # Debugging check

        # Save updates back to the same file
        df.to_csv(file_path, index=False, quoting=1)

        # Update current dataset
        new_data = process_uploaded_data(file_path, input.number_matches_considered())

        # Adjust index if necessary
        new_index = min(current_index(), max(0, len(new_data) - 1))
        current_index.set(new_index)

        # Update reactive data
        current_data.set(new_data)

    @reactive.effect
    @reactive.event(input.matches_upload)
    def handle_upload():
        if input.matches_upload() is not None:

            df = load_data()
            if df is not None:
                # Update the dropdown choices based on available columns
                distance_options = [col for col in df.columns if col.endswith('_values')]

                ui.update_select(
                    "selected_algorithm",
                    choices=distance_options,
                    selected=distance_options[0] if distance_options else None
                )



    @reactive.effect
    @reactive.event(input.selected_algorithm)
    def handle_algo_select():
        if input.matches_upload is None or not input.selected_algorithm():
            return None

        # Process the uploaded data
        file_path = input.matches_upload()[0]["datapath"]
        processed_data = process_uploaded_data(file_path, input.selected_algorithm(), input.number_matches_considered())

        # Update the reactive values
        current_data.set(processed_data)
        current_index.set(0)


    @reactive.effect
    @reactive.event(input.number_matches_considered)
    def update_on_number_matches_change():
        if input.matches_upload() is not None:
            file_path = input.matches_upload()[0]["datapath"]
            processed_data = process_uploaded_data(file_path, input.selected_algorithm(), input.number_matches_considered())

            current_data.set(processed_data)
            current_index.set(0)


    @reactive.effect
    @reactive.event(input.prev_image, input.next_image, input.no_matches)
    def handle_navigation():
        if current_data() is None:
            return

        if input.prev_image.get() and current_index() > 0:
            current_index.set(current_index() - 1)
        elif input.next_image.get() and current_index() < len(current_data()) - 1:
            current_index.set(current_index() + 1)
        elif input.no_matches.get():
            row = current_data().iloc[current_index()]
            update_matches(row["focal_name"])
            if current_index() < len(current_data()) - 1:
                current_index.set(current_index() + 1)


    @reactive.effect
    @reactive.event(lambda: [input[f"match_button_{i}"]() for i in range(get_test_images_length())])
    def handle_match_clicks():
        if current_data() is None:  # Early return if no data
            return

        # Now we can safely get the number of test images
        row = current_data().iloc[current_index()]
        n = len(row["test_name"])

        # Check each button's current state
        current_states = {}
        was_clicked = []

        # Only iterate over the actual number of buttons
        for i in range(n):
            btn_id = f"match_button_{i}"
            try:
                current_value = input[btn_id]()
                previous_value = button_states.get().get(btn_id, 0)

                current_states[btn_id] = current_value

                if current_value > previous_value:
                    was_clicked.append(i)
            except Exception:
                continue  # Skip if button doesn't exist

        button_states.set(current_states)

        if was_clicked:
            row = current_data().iloc[current_index()]
            for i in was_clicked:
                update_matches(row["focal_name"], row["test_name"][i])

    @output
    @render.ui
    def main_interface():
        if current_data() is None:
            return ui.p("Please upload a CSV file to begin.")

        return ui.card(
            ui.card_header("Image Comparison Viewer"),
            ui.card_body(
                ui.row(
                    ui.column(
                        6,
                        ui.card(
                            ui.card_header("Focal Image"),
                            ui.card_body(
                                {"style": "height: 65vh; overflow-y: auto;"},
                                ui.output_ui("focal_image"),
                                ui.div(
                                    ui.input_action_button("prev_image", "Previous", style=BUTTON_STYLE),
                                    ui.input_action_button("no_matches", "No Matches Here", style=BUTTON_STYLE),
                                    ui.input_action_button("next_image", "Next", style=BUTTON_STYLE),
                                    style="text-align: center; margin-top: 20px;",
                                ),
                            ),
                        ),
                    ),
                    ui.column(
                        6,
                        ui.card(
                            ui.card_header("Matching Images with Information"),
                            ui.card_body(
                                {"style": "height: 65vh; overflow-y: auto;"},
                                ui.output_ui("matching_images"),
                            ),
                        ),
                    ),
                )
            ),
            style="height: 75vh; overflow: hidden;",
        )

    @output
    @render.ui
    def focal_image():
        if current_data() is None or len(current_data()) == 0:
            return ""
        row = current_data().iloc[current_index()]

        # Construct the path for the focal image
        focal_image_path = os.path.join(
            "fingerprints", row["focal_image"], f"{row['focal_image']}_img.png"
        )
        print(focal_image_path)

        return ui.div(
            ui.tags.img(src=focal_image_path, style=IMAGE_STYLE),
            ui.div(
                f"Focal Name: {row['focal_name']} | Focal Size: {row['focal_size']:.3f}",
                style="padding: 5px; border-radius: 5px; margin-top: 10px; text-align: center;",
            ),
        )

    @output
    @render.ui
    def matching_images():
        if current_data() is None or len(current_data()) == 0:
            return ""

        row = current_data().iloc[current_index()]
        n_buttons = len(row["test_image"])
        image_rows = []

        for i, (img, name, sim, size) in enumerate(zip(
                row["test_image"], row["test_name"],
                row[input.selected_algorithm()], row["test_size"])):
            # Construct the path for each test image
            test_image_path = os.path.join(
                "fingerprints", img, f"{img}_img.png"
            )

            image_rows.append(ui.div(
                ui.tags.img(src=test_image_path, style=IMAGE_STYLE),
                ui.div(
                    f"Name: {name} | Distance: {float(sim):.3f} | Size: {float(size):.3f}",
                    style="padding: 5px; border-radius: 5px; margin-bottom: 10px; text-align: center;",
                ),
                ui.input_action_button(
                    f"match_button_{i}",
                    "This is a match",
                    style="display: block; margin: 0 auto; margin-bottom: 30px;",
                ),
                style="margin-bottom: 30px;",
            ))

        return ui.div(image_rows)
