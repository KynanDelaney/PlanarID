from shiny import ui, render, reactive
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from datetime import date


def generate_and_visualise_encounter_history_page_ui():
    return ui.nav_panel(
        "Generate and Visualise Encounter History",
        ui.card(
            ui.card_header("Upload Confirmed Matches"),
            ui.card_body(
                ui.row(
                    ui.column(6,
                              ui.input_file("alias_upload", "Choose CSV file", accept=[".csv"])
                              ),
                    ui.column(6,
                              ui.row(ui.input_checkbox("render_graph", "Render graph", value=False),
                                     ),
                              ui.row(ui.input_action_button("save_encounters", "Save parameters",
                                                            class_="btn-primary", width="35%"),
                                     ),
                              ),
                )
            )
        ),
        ui.card(
            ui.output_ui("encounter_information")
        ),
        ui.card(
            {"style": "height: 80vh; width: 80vh; margin: 20px auto;"},  # Make card square and centered
            ui.h3("Visualise Pattern Clusters"),
            ui.output_plot("pattern_clusters", height="80vh", width="80vh")
        ),
    )


def generate_and_visualise_encounter_history_page_server(input, output, session, BASE_DIR):
    @reactive.calc
    def load_data():
        upload = input.alias_upload()
        if upload:
            try:
                file_path = upload[0]["datapath"]
                df = pd.read_csv(file_path)
                # Basic validation
                required_cols = ['focal_name', 'test_name']
                if not all(col in df.columns for col in required_cols):
                    return pd.DataFrame(), f"Missing required columns: {required_cols}"
                return df, None
            except Exception as e:
                return pd.DataFrame(), f"Error loading file: {str(e)}"
        return pd.DataFrame(), None

    def convert_matches_to_chains(df):
        G = nx.from_pandas_edgelist(df, 'focal_name', 'test_name')
        components = list(nx.connected_components(G))
        chain_map = {}
        for i, component in enumerate(components):
            for node in component:
                chain_map[node] = f'Individual_{i + 1}'
        df['individual'] = df['focal_name'].map(chain_map)
        return df, G

    def convert_chains_to_census(df):
        # Pivot longer
        df_long = pd.melt(df, id_vars=['individual'], value_vars=['focal_name', 'test_name'],
                          value_name='alias').drop(columns=['variable'])
        # Remove duplicates
        df_unique = df_long.drop_duplicates(subset=['alias', 'individual'])
        return df_unique

    def create_encounter_tables(df):
        # Count occurrences
        individual_counts = df['individual'].value_counts().reset_index()
        individual_counts.columns = ['Individual ID', 'Number of encounters']  # Custom headers

        count_summary = individual_counts['Number of encounters'].value_counts().reset_index(name='num_individuals')
        count_summary.columns = ['Number of encounters', 'Number of individuals with this history']  # Custom headers
        return individual_counts, count_summary


    # Reactive calculations for tables
    @reactive.calc
    def processed_data():
        df, error = load_data()
        if error or df.empty:
            return None, None, error

        try:
            df, G = convert_matches_to_chains(df)
            census_df = convert_chains_to_census(df)
            individual_counts, count_summary = create_encounter_tables(census_df)
            return individual_counts, count_summary, None
        except Exception as e:
            return None, None, f"Error processing data: {str(e)}"

    @render.plot
    @reactive.event(input.alias_upload, input.render_graph)
    def pattern_clusters():
        df, error = load_data()
        if error:
            # Could return an error plot here
            return None

        if not input.render_graph() or df.empty:
            return None

        try:
            df, G = convert_matches_to_chains(df)

            plt.clf()
            fig, ax = plt.subplots(figsize=(10, 10))
            pos = nx.spring_layout(G)
            nx.draw(
                G, pos, with_labels=True, node_size=3000, node_color="skyblue",
                font_size=10, font_color="black", edge_color="gray", ax=ax
            )
            plt.tight_layout()
            return fig
        except Exception as e:
            # Return error plot
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, f"Error creating graph: {str(e)}",
                    ha='center', va='center', transform=ax.transAxes)
            return fig

    @render.ui
    def encounter_information():
        individual_counts, count_summary, error = processed_data()

        if error:
            return ui.div(
                ui.p(f"Error: {error}", style="color: red;")
            )

        if individual_counts is None:
            return ui.p("Please upload data to view encounter information.")

        # Calculate the number of unique individuals
        num_unique_individuals = individual_counts.shape[0]

        return ui.div(
            ui.tags.style("""
                .aligned-table th, .aligned-table td {
                    text-align: left !important;
                }
                .scrollable-table {
                    max-height: 400px;
                    overflow-y: auto;
                    border: 1px solid #dee2e6;
                    border-radius: 0.375rem;
                }
            """),
            ui.h3("Encounter Data"),
            ui.p(f"Number of individuals present in this photographic record: {num_unique_individuals}"),
            ui.row(
                ui.column(6,
                          ui.h4("Individual-level"),
                          ui.div(
                              ui.HTML(
                                  individual_counts.to_html(index=False, classes="table table-striped aligned-table")),
                              class_="scrollable-table"
                          )
                          ),
                ui.column(6,
                          ui.h4("Population-level"),
                          ui.div(
                              ui.HTML(count_summary.to_html(index=False, classes="table table-striped aligned-table")),
                              class_="scrollable-table"
                          )
                          )
            )
        )

    @reactive.effect
    @reactive.event(input.save_encounters)
    def _():
        df, error = load_data()
        if error or df.empty:
            ui.notification_show("Please upload data first!", type="error")
            return

        try:
            # Process the data to get df_unique
            df, _ = convert_matches_to_chains(df)
            df_unique = convert_chains_to_census(df)

            print(df_unique)

            df_unique['encounter_occasion'] = df_unique['alias'].apply(lambda x: x.split("_")[0])

            # Save the file
            output_file = BASE_DIR / 'data' / f'encounter_history_{date.today()}.csv'
            df_unique.to_csv(output_file, mode='w', header=True, index=False)

            ui.notification_show("Encounter history saved!", type="message")

        except Exception as e:
            ui.notification_show(f"Error saving file: {str(e)}", type="error")
