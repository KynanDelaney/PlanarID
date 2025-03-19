from shiny import ui, render, reactive
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx




def within_individual_comparison_page_ui():
    return ui.nav_panel(
        "Within-Individual Quality Control",
        ui.card(
            ui.card_header("Input Selection"),
            ui.card_body(
                ui.row(
                    ui.column(6,
                              ui.input_file("csv_upload", "Choose CSV file", accept=[".csv"])
                              ),
                    ui.column(3,
                              ui.input_select(
                                  "selected_individual",
                                  "Select Individual",
                                  choices=[]
                              )
                              ),
                    ui.column(3,
                              ui.input_select("selected_metric", "Choice of algorithm:", choices=[])
                              )
                )
            )
        ),
        ui.card(
            {"style": "height: 80vh; width: 80vh; margin: 20px auto;"},  # Make card square and centered
            ui.card_header("Image Similarity Network"),
            ui.output_plot("network", height="65vh", width="65vh")  # Make plot square within card
        ),
        ui.card(
            ui.card_header("Image Gallery"),
            ui.output_ui("image_gallery")
        )
    )


def within_individual_comparison_page_server(input, output, session):
    def load_data():
        if input.csv_upload() is not None:
            file_path = input.csv_upload()[0]["datapath"]
            df = pd.read_csv(file_path)
            return df
        return None

    @render.plot
    @reactive.event(input.selected_individual, input.selected_metric)
    def network():
        df = load_data()
        if df is None or not input.selected_individual() or not input.selected_metric():
            return None

        plt.clf()

        # Filter data for within-individual comparisons only
        individual_data = df[
            (df['focal_name'] == input.selected_individual()) &
            (df['test_name'] == input.selected_individual())
            ]

        if len(individual_data) == 0:
            return None

        # Create network graph
        G = nx.Graph()

        # Create mapping of image paths to names
        image_to_name = {}
        for _, row in individual_data.iterrows():
            image_to_name[row['focal_image']] = row['focal_name']
            image_to_name[row['test_image']] = row['test_name']

        # Add all edges with their similarities
        for _, row in individual_data.iterrows():
            # Invert similarity to distance (lower similarity = shorter distance)
            # Add a small constant to avoid division by zero
            distance = 1 / (float(row[input.selected_metric()]) + 1e-6)
            G.add_edge(row['focal_image'], row['test_image'],
                       weight=distance,  # Used for layout
                       similarity=float(row[input.selected_metric()]))  # Original similarity for display

        if len(G.edges()) == 0:
            return None

        # Create figure
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111)

        # Use weight (distance) for layout
        pos = nx.spring_layout(G, k=1, iterations=50, weight='weight')

        # Draw the network
        nx.draw_networkx_edges(G, pos, width=2, alpha=0.6)

        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=1000)

        # Use the image names as labels instead of individual names
        # This is the key change - we now use the node names directly as labels
        labels = {node: node for node in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels, font_size=10)

        # Add similarity values as edge labels
        edge_labels = nx.get_edge_attributes(G, 'similarity')
        edge_labels = {k: f'{v:.2f}' for k, v in edge_labels.items()}
        nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=8)

        # Set fixed axis limits
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)

        ax.set_title(
            f"Within-Individual Image Dissimilarity Network for {input.selected_individual()}\n"
            f"(Edge lengths proportional to 'distance')")
        ax.axis('off')
        return fig


    @render.ui
    @reactive.event(input.selected_individual)
    def image_gallery():
        df = load_data()
        if df is None or not input.selected_individual():
            return None

        # Get unique focal images and test images for the selected individual
        all_individual_images = pd.concat([
            df[df['focal_name'] == input.selected_individual()]['focal_image'],
            df[df['test_name'] == input.selected_individual()]['test_image']
        ]).unique()

        # Create a grid of images using ui.row and ui.column
        gallery_rows = []
        images_per_row = 4

        for i in range(0, len(all_individual_images), images_per_row):
            row_images = all_individual_images[i:i + images_per_row]
            cols = []

            for img in row_images:
                img_path = f"fingerprints/{img}/{img}_img.png"
                cols.append(
                    ui.column(3,  # 12/4 = 3 for 4 images per row
                              ui.card(
                                  ui.card_body(
                                      ui.img({"src": img_path, "style": "width: 100%; height: auto;"}),
                                      ui.p(img, style="text-align: center; margin-top: 10px;")
                                  )
                              )
                              )
                )

            gallery_rows.append(ui.row(*cols, style="margin-bottom: 20px;"))

        return ui.div(*gallery_rows)

    @reactive.effect
    @reactive.event(input.csv_upload)
    def _():
        df = load_data()
        if df is not None:
            # Get unique individual names
            individuals = sorted(df['focal_name'].unique())
            ui.update_select(
                "selected_individual",
                choices=individuals,
                selected=individuals[0] if individuals else None
            )

            # Update the dropdown choices based on available columns
            distance_options = [col for col in df.columns if col.endswith('_values')]

            ui.update_select(
                "selected_metric",
                choices=distance_options,
                selected=distance_options[0] if distance_options else None
            )
