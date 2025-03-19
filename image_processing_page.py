from shiny import ui, render, reactive
import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image
import pandas as pd
import os


def check_surf_available():
    """Check if SURF feature detector is available"""
    try:
        import cv2
        surf = cv2.xfeatures2d.SURF_create()
        return True
    except (ImportError, AttributeError):
        return False

def load_user_parameters(csv_path):
    """Load user parameters from CSV into a dictionary."""
    try:
        df = pd.read_csv(csv_path)
        parameters = dict(zip(df["Parameter"], df["Value"]))
        print(f"Loaded parameters from '{csv_path}'.")
        return parameters
    except Exception as e:
        print(f"Error loading parameters: {e}")
        return {}


def image_processing_page_ui(BASE_DIR):
    # Check SURF availability at UI creation time
    surf_available = check_surf_available()

    # Load user parameters
    user_parameters = load_user_parameters(os.path.join(BASE_DIR, "data/user_parameters.csv"))

    # Create the fingerprint and comparison options dictionaries
    fingerprint_options = {
        "akaze_fingerprint": "AKAZE",
        "orb_fingerprint": "ORB",
        "sift_fingerprint": "SIFT"
    }

    if surf_available:
        fingerprint_options["surf_fingerprint"] = "SURF"

    return ui.nav_panel("Image Processing",
        ui.head_content(
            ui.tags.style("""
                .image-container {
                    width: 100%;
                    padding-top: 75%;
                    position: relative;
                    overflow: hidden;
                    border: 2px solid #ddd;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                }
                .image-container img {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    object-fit: contain;
                }
                .scrolling-sidebar {
                    height: calc(100vh - 60px); /* Adjust based on your navbar height */
                    overflow-y: auto;
                    position: sticky;
                    top: 0;
                    padding-right: 15px;
                }
            """)
        ),
        ui.row(
            ui.column(3, ui.div(
                ui.h2("Image Processing Controls"),
                ui.h3("HSV Colour Thresholds"),
                ui.layout_columns(
                    ui.column(6,
                        ui.h4("Lower HSV"),
                        ui.input_numeric("hue_low", "Hue", min=0, max=179, value=user_parameters.get("hue_low", 0)),
                        ui.input_numeric("saturation_low", "Saturation", min=0, max=255, value=user_parameters.get("saturation_low", 0)),
                        ui.input_numeric("value_low", "Value", min=0, max=255, value=user_parameters.get("value_low", 0)),
                    ),
                    ui.column(6,
                        ui.h4("Upper HSV"),
                        ui.input_numeric("hue_high", "Hue", min=0, max=179, value=user_parameters.get("hue_high", 179)),
                        ui.input_numeric("saturation_high", "Saturation", min=0, max=255, value=user_parameters.get("saturation_high", 255)),
                        ui.input_numeric("value_high", "Value", min=0, max=255, value=user_parameters.get("value_high", 255)),
                    )
                ),
                ui.output_ui("color_swatches"),
                ui.h3("Processing Thresholds"),
                ui.input_slider("kernel_size", "Kernel Size - Applies smoothing to contours", min=1, max=51, value=user_parameters.get("kernel_size", 11), step=2),
                ui.input_numeric("threshold_value", "Threshold value - Greyscale cut-off", min=0, max=255, value=user_parameters.get("threshold_value", 50)),
                ui.input_numeric("num_patches", "Number of colour patches", min=0, max=20, value=user_parameters.get("num_patches", 4), step=1),
                ui.input_numeric("min_area", "Minimum patch size (pixels)", min=0, max=20000, value=user_parameters.get("min_area", 7500), step=5),
                ui.input_slider("mult", "Border around pattern", min=1, max=2, value=user_parameters.get("mult", 1.1), step=0.1),
                ui.h3("Fingerprint Thresholds"),
                ui.input_slider("hessian_threshold", "Hessian threshold - Decrease sensitivity", min=50, max=10000, value=user_parameters.get("hessian_threshold", 500), step=50),
                ui.input_numeric("n_features", "Number of features", min=100, max=5000, value=user_parameters.get("n_features", 1000), step=50),
                ui.input_slider("akaze_threshold", "AKAZE threshold - Decrease sensitivity", min=0.0001, max=0.01,
                                value=user_parameters.get("akaze_threshold", 0.001), step=.0005),
                ui.h3("Rendered Output"),
                ui.input_select("output_type",
                                "Output image type:",
                              {
                                    "Visualise Pre-processing": {"Initial Segmentation":"Initial Segmentation", "Contours":"Contours", "Annotated Pattern":"Annotated Pattern", "Filtered Mask":"Filtered Mask - For Algorithms", "Cropped Output":"Cropped Output - For Humans"},
                                       "Visualise Fingerprint Algorithms": fingerprint_options}),
                ui.h3("Additional parameters - Effects elsewhere"),
                ui.input_numeric("cutoff_size", "Expected max. mask size (pixels)", min=0, max=25000000, value=user_parameters.get("cutoff_size", 6000000), step=1),
                ui.input_numeric("size_offset", "Accepted body size difference (units)", min=0, max=1000, value=user_parameters.get("size_offset", 50), step=.01),
                ui.input_numeric("number_comparisons_considered", "Number of pairwise comparisons considered", min=1, max=40,
                                 value=user_parameters.get("number_comparisons_considered", 20), step=1),
                ui.input_action_button("save", "Save parameters"),
                ui.div(style="height: 20px"),
            ), class_="scrolling-sidebar"
                      ),

            ui.column(9, ui.div(
                ui.h3("Single Image Processing"),
                ui.layout_columns(
                    ui.column(6,
                              ui.input_file("file_single", "Choose an image (JPEG or PNG)", accept=[".jpg", ".jpeg", ".png"]),
                              ),
                    ui.column(6,
                              ui.input_checkbox("downgrade_image", "Reduce image quality", value = False),
                              ),
                ),
                ui.output_ui("single_image_output"),
            ), class_="main-content"
            )
        )
    )

def image_processing_page_server(input, output, session, BASE_DIR):
    original_image = reactive.value(None)
    single_image = reactive.value(None)

    @reactive.effect
    @reactive.event(input.file_single)
    def _():
        file_info = input.file_single()
        if file_info and file_info[0]['datapath']:
            img = cv2.imread(file_info[0]['datapath'], cv2.IMREAD_UNCHANGED)
            if img is not None:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                original_image.set(img)

    @reactive.effect
    def _():
        img = original_image.get()
        if img is not None:
            if input.downgrade_image():
                height, width = img.shape[:2]
                small = cv2.resize(img, (width // 8, height // 8), interpolation=cv2.INTER_AREA)
                processed_img = cv2.resize(small, (width, height), interpolation=cv2.INTER_LINEAR)
                single_image.set(processed_img)
            else:
                single_image.set(img)

    def image_to_base64(img):
        pil_img = Image.fromarray(img)
        buffered = BytesIO()
        pil_img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    def process_image(img):
        # convert image to grey and HSV formats for simpler calculations, get some basic info about image size
        img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        height, width, _ = img.shape
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)

        # apply HSV colour thresholding for binary mask - identifying regions likely to do with pattern
        lower_hsv = np.array([input.hue_low(), input.saturation_low(), input.value_low()])
        upper_hsv = np.array([input.hue_high(), input.saturation_high(), input.value_high()])
        mask = cv2.inRange(hsv, lower_hsv, upper_hsv)

        mask_result = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)


        # use mask to highlight regions of interest. apply blur to smooth out rough edges, and then find the outline (contour) of all relevant colour regions
        focal_regions = cv2.bitwise_and(img, img, mask=mask)
        blurred_regions = cv2.medianBlur(focal_regions, input.kernel_size())
        blur_gray = cv2.cvtColor(blurred_regions, cv2.COLOR_RGB2GRAY)
        ret, thresh = cv2.threshold(blur_gray, input.threshold_value(), 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # apply some checks - removing really small patches of colour, keeping only the largest regions most likely to be associated with patterns
        areas = [cv2.contourArea(contour) for contour in contours]
        patches = [areas.index(k) for k in sorted(areas, reverse=True)][:input.num_patches()]
        conts = []
        for p in patches:
            if areas[p] > input.min_area():
                conts.append(contours[p])

        countour_result = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
        cv2.drawContours(countour_result, conts, -1, (0, 255, 0), 2)

        # redefining our colour mask based on the above filtering - removes noise for pattern extraction.
        # Step 1: Create a blank mask to start fresh
        filled_mask = np.zeros_like(mask)

        # Step 2: Draw the filtered contours onto the new mask
        for contour in conts:
            cv2.drawContours(filled_mask, [contour], -1, 255, thickness=-1)

        # Step 3: Apply the filled mask to the original image
        # Convert the single-channel mask to match the dimensions of the original image
        filtered_mask = cv2.cvtColor(filled_mask, cv2.COLOR_GRAY2BGR)

        # Use bitwise_and to apply the mask to the original image
        filtered_mask = cv2.bitwise_and(img, filtered_mask)

        length = len(conts)
        cont = np.vstack([conts[q] for q in range(length)])
        #cont = np.vstack(conts[q] for q in range(length))
        rect = cv2.minAreaRect(cont)
        box = cv2.boxPoints(rect)
        box = np.int32(box)

        img1 = img.copy()  # Create a copy of the image
        box_result = cv2.drawContours(img1, [box], 0, (0, 255, 0), 10)

        W = rect[1][0]
        H = rect[1][1]
        Xs = [r[0] for r in box]
        Ys = [s[1] for s in box]
        x1 = min(Xs)
        x2 = max(Xs)
        y1 = min(Ys)
        y2 = max(Ys)

        rotated = False
        angle = rect[2]
        if angle < -45:
            angle += 90
            rotated = True

        center = (int((x1 + x2) / 2), int((y1 + y2) / 2))
        size = (int(input.mult() * (x2 - x1)), int(input.mult() * (y2 - y1)))

        M = cv2.getRotationMatrix2D((size[0] / 2, size[1] / 2), angle, 1.0)
        cropped_W = W if not rotated else H
        cropped_H = H if not rotated else W

        cropped_mask = cv2.getRectSubPix(filtered_mask, size, center)
        cropped_mask = cv2.warpAffine(cropped_mask, M, size)
        cropped_Rotated_mask = cv2.getRectSubPix(cropped_mask, (int(cropped_W * input.mult()), int(cropped_H * input.mult())),
                                                (size[0] / 2, size[1] / 2))

        cropped_img = cv2.getRectSubPix(img, size, center)
        cropped_img = cv2.warpAffine(cropped_img, M, size)
        cropped_Rotated_img = cv2.getRectSubPix(cropped_img, (int(cropped_W * input.mult()), int(cropped_H * input.mult())),
                                               (size[0] / 2, size[1] / 2))

        output_type = input.output_type()

        fingerprint_blank = cropped_Rotated_img.copy()
        fingerprint_blank = cv2.cvtColor(fingerprint_blank, cv2.COLOR_RGB2GRAY)

        if output_type == "Initial Segmentation":
            result = mask_result
        elif output_type == "Contours":
            result = countour_result
        elif output_type  == "Annotated Pattern":
            result = box_result
        elif output_type == "Filtered Mask":
            result = cropped_Rotated_mask
        elif output_type == "Cropped Output":
            result = cropped_Rotated_img
        elif output_type == "surf_fingerprint":
            surf = cv2.xfeatures2d.SURF_create(input.hessian_threshold())
            surf_kp, surf_desc = surf.detectAndCompute(cropped_Rotated_mask, None)
            result = cv2.drawKeypoints(fingerprint_blank, surf_kp, None, (0, 255, 0), 4)
        elif output_type == "sift_fingerprint":
            sift = cv2.SIFT_create(nfeatures=input.n_features())
            sift_kp, sift_desc = sift.detectAndCompute(cropped_Rotated_mask, None)
            result = cv2.drawKeypoints(fingerprint_blank, sift_kp, None, (0, 255, 0), 4)
        elif output_type == "orb_fingerprint":
            orb = cv2.ORB_create(nfeatures=input.n_features())
            orb_kp, orb_desc = orb.detectAndCompute(cropped_Rotated_mask, None)
            result = cv2.drawKeypoints(fingerprint_blank, orb_kp, None, (0, 255, 0), 4)
        elif output_type == "akaze_fingerprint":
            akaze = cv2.AKAZE_create(threshold = input.akaze_threshold())
            akaze_kp, akaze_desc = akaze.detectAndCompute(cropped_Rotated_mask, None)
            result = cv2.drawKeypoints(fingerprint_blank, akaze_kp, None, (0, 255, 0), 4)

        return result

    @output
    @render.ui
    def single_image_output():
        if single_image() is None:
            return "Please upload an image."

        processed_img = process_image(single_image())
        original_img_str = image_to_base64(single_image())
        processed_img_str = image_to_base64(processed_img)

        return ui.div(
            ui.row(
                ui.column(6,
                    ui.h3("Original Image"),
                    ui.div(
                        ui.tags.img(src=f"data:image/png;base64,{original_img_str}"),
                        class_="image-container"
                    )
                ),
                ui.column(6,
                    ui.h3("Processed Image"),
                    ui.div(
                        ui.tags.img(src=f"data:image/png;base64,{processed_img_str}"),
                        class_="image-container"
                    )
                )
            )
        )

    @output
    @render.ui
    def color_swatches():
        h_low, s_low, v_low = input.hue_low(), input.saturation_low(), input.value_low()
        h_high, s_high, v_high = input.hue_high(), input.saturation_high(), input.value_high()

        color_low = np.uint8([[[h_low, s_low, v_low]]])
        color_high = np.uint8([[[h_high, s_high, v_high]]])

        rgb_low = cv2.cvtColor(color_low, cv2.COLOR_HSV2RGB)[0][0]
        rgb_high = cv2.cvtColor(color_high, cv2.COLOR_HSV2RGB)[0][0]

        hex_low = '#{:02x}{:02x}{:02x}'.format(rgb_low[0], rgb_low[1], rgb_low[2])
        hex_high = '#{:02x}{:02x}{:02x}'.format(rgb_high[0], rgb_high[1], rgb_high[2])

        return ui.div(
            ui.layout_columns(
                ui.column(6,
                    ui.div(style=f"width: 100%; height: 50px; background-color: {hex_low}; margin-top: 10px;")),
                ui.column(6,
                    ui.div(style=f"width: 100%; height: 50px; background-color: {hex_high}; margin-top: 10px;"))
            )
        )

    @reactive.effect
    @reactive.event(input.save)
    def _():
        params = pd.DataFrame({
            'Parameter': ['hue_low', 'saturation_low', 'value_low',
                          'hue_high', 'saturation_high', 'value_high',
                          'kernel_size', 'threshold_value',
                          'num_patches', 'min_area', 'mult',
                          'hessian_threshold', 'n_features', 'akaze_threshold',
                          'cutoff_size', 'size_offset', 'number_comparisons_considered'],
            'Value': [input.hue_low(), input.saturation_low(), input.value_low(),
                      input.hue_high(), input.saturation_high(), input.value_high(),
                      input.kernel_size(), input.threshold_value(),
                      input.num_patches(), input.min_area(), input.mult(),
                      input.hessian_threshold(), input.n_features(), input.akaze_threshold(),
                      input.cutoff_size(), input.size_offset(), input.number_comparisons_considered()]
        })

        # Always write with header, overwriting any existing file
        params.to_csv(os.path.join(BASE_DIR, "data/user_parameters.csv"), mode='w', header=True, index=False)

        ui.notification_show("Parameters saved", type="message")
