from shiny import ui, render, reactive
import os
import cv2
import numpy as np
import pandas as pd
from io import BytesIO
from PIL import Image
import base64


def check_surf_available():
    """Check if SURF feature detector is available"""
    try:
        import cv2
        surf = cv2.xfeatures2d.SURF_create()
        return True
    except (ImportError, AttributeError):
        return False


def get_files(BASE_DIR):
    """Modified to accept BASE_DIR parameter"""
    path = os.path.join(BASE_DIR, "unprocessed_photos")
    return sorted([f for f in os.listdir(path)
                   if os.path.isfile(os.path.join(path, f)) and not f.startswith('.')])


def example_matching_page_ui():
    # Check SURF availability at UI creation time
    surf_available = check_surf_available()

    # Create the fingerprint and comparison options dictionaries
    fingerprint_options = {
        "akaze_fingerprint": "AKAZE",
        "orb_fingerprint": "ORB",
        "sift_fingerprint": "SIFT"
    }

    if surf_available:
        fingerprint_options["surf_fingerprint"] = "SURF"

    return ui.nav_panel("Visualise Fingerprint Matching",
                        ui.row(
                            ui.column(3,
                                      ui.div(
                                          ui.h2("Individual and Algorithm Selector"),
                                          ui.input_select("individualA", "Select first individual",
                                                          choices=[], selected=None),
                                          ui.input_select("individualB", "Select second individual",
                                                          choices=[], selected=None),
                                          ui.input_select(
                                              "fingerprint",
                                              "Fingerprint Type:",
                                              fingerprint_options
                                          ),
                                          ui.input_slider("number_points", "Limit number of matches",
                                                          min=10, max=100, value=20, step=5
                                                          ),
                                      ),
                                      ),
                            ui.column(9,
                                      ui.output_ui("visualise_matched_fingerprints"),
                                      )
                        )
                        )


def example_matching_page_server(input, output, session, BASE_DIR):
    @reactive.Effect
    def _():
        choices = get_files(BASE_DIR)
        ui.update_select("individualA", choices=choices)
        ui.update_select("individualB", choices=choices)

    # Read parameters once at startup
    df = pd.read_csv(os.path.join(BASE_DIR, "data/user_parameters.csv"))
    params = {row["Parameter"]: float(row["Value"]) for _, row in df.iterrows()}

    # Reactive values for both images
    processed_image1 = reactive.value((None, None))
    processed_image2 = reactive.value((None, None))

    def image_to_base64(img):
        if img is None:
            return None
        pil_img = Image.fromarray(img)
        buffered = BytesIO()
        pil_img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    def process_image(img):
        if img is None:
            return None

        # Extract parameters from the loaded dictionary
        lower = (int(params["hue_low"]), int(params["saturation_low"]), int(params["value_low"]))
        upper = (int(params["hue_high"]), int(params["saturation_high"]), int(params["value_high"]))
        kernel_size = int(params["kernel_size"])
        threshold_value = int(params["threshold_value"])
        num_patches = int(params["num_patches"])
        min_area = int(params["min_area"])
        mult = float(params["mult"])

        # convert image to HSV format
        height, width, _ = img.shape
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)

        # apply HSV colour thresholding
        mask = cv2.inRange(hsv, lower, upper)

        # Process regions of interest
        focal_regions = cv2.bitwise_and(img, img, mask=mask)
        blurred_regions = cv2.medianBlur(focal_regions, kernel_size)
        blur_gray = cv2.cvtColor(blurred_regions, cv2.COLOR_RGB2GRAY)
        ret, thresh = cv2.threshold(blur_gray, threshold_value, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        # Filter contours
        areas = [cv2.contourArea(contour) for contour in contours]
        patches = [areas.index(k) for k in sorted(areas, reverse=True)][:num_patches]
        conts = []
        for p in patches:
            if areas[p] > min_area:
                conts.append(contours[p])

        if not conts:
            return None

        # Create mask from filtered contours
        filled_mask = np.zeros_like(mask)
        for contour in conts:
            cv2.drawContours(filled_mask, [contour], -1, 255, thickness=-1)

        # Apply mask to original image
        filtered_mask = cv2.cvtColor(filled_mask, cv2.COLOR_GRAY2BGR)

        # Get bounding rectangle
        length = len(conts)
        cont = np.vstack([conts[q] for q in range(length)])
        rect = cv2.minAreaRect(cont)
        box = cv2.boxPoints(rect)
        box = np.int32(box)

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
        size = (int(mult * (x2 - x1)), int(mult * (y2 - y1)))

        M = cv2.getRotationMatrix2D((size[0] / 2, size[1] / 2), angle, 1.0)
        cropped_W = W if not rotated else H
        cropped_H = H if not rotated else W

        cropped_img = cv2.getRectSubPix(img, size, center)
        cropped_img = cv2.warpAffine(cropped_img, M, size)
        cropped_Rotated_img = cv2.getRectSubPix(cropped_img,
                                                (int(cropped_W * mult), int(cropped_H * mult)),
                                                (size[0] / 2, size[1] / 2))

        cropped_mask = cv2.getRectSubPix(filtered_mask, size, center)
        cropped_mask = cv2.warpAffine(cropped_mask, M, size)
        cropped_Rotated_mask = cv2.getRectSubPix(cropped_mask,
                                                 (int(cropped_W * input.mult()), int(cropped_H * input.mult())),
                                                 (size[0] / 2, size[1] / 2))

        return cropped_Rotated_img, cropped_Rotated_mask


    @reactive.effect
    @reactive.event(input.individualA, input.individualB)
    def _():
        if input.individualA() is not None:
            img1 = cv2.imread(os.path.join(BASE_DIR, "unprocessed_photos", input.individualA()))
            if img1 is not None:
                img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
                processed_image1.set(process_image(img1))

        if input.individualB() is not None:
            img2 = cv2.imread(os.path.join(BASE_DIR, "unprocessed_photos", input.individualB()))
            if img2 is not None:
                img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)
                processed_image2.set(process_image(img2))

    def compare_matched_fingerprints():
        img1_data = processed_image1.get()
        img2_data = processed_image2.get()

        if img1_data[0] is None or img2_data[0] is None:
            return None

        img1, mask1 = img1_data
        img2, mask2 = img2_data

        # Convert to grayscale
        gray1 = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY)

        # Convert masks to single channel if they're not already
        if len(mask1.shape) > 2:
            mask1 = cv2.cvtColor(mask1, cv2.COLOR_BGR2GRAY)
        if len(mask2.shape) > 2:
            mask2 = cv2.cvtColor(mask2, cv2.COLOR_BGR2GRAY)

        # Initialize feature detector based on selection
        if input.fingerprint() == "orb_fingerprint":
            detector = cv2.ORB_create(nfeatures=int(params["n_features"]))
        elif input.fingerprint() == "sift_fingerprint":
            detector = cv2.SIFT_create(nfeatures=int(params["n_features"]))
        elif input.fingerprint() == "surf_fingerprint":
            detector = cv2.xfeatures2d.SURF_create(int(params["hessian_threshold"]))
        else:  # AKAZE default
            detector = cv2.AKAZE_create(threshold=float(params["akaze_threshold"]))


        # Detect and compute keypoints and descriptors using masks
        kp1, des1 = detector.detectAndCompute(gray1, mask1)
        kp2, des2 = detector.detectAndCompute(gray2, mask2)

        # Create matcher
        if input.fingerprint() in ["akaze_fingerprint", "orb_fingerprint"]:
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck = True)
        else:
            bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck = True)

        # Match descriptors
        matches = bf.match(des1, des2)

        sorted_matches = sorted(matches, key=lambda x: x.distance)

        # Draw matches (make sure we have matches to draw)
        if len(sorted_matches) > 0:
            matched_img = cv2.drawMatches(gray1,kp1,gray2,kp2,sorted_matches[:input.number_points()],None,
                          flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
                          matchColor=(0, 255, 0))
        else:
            # If no matches found, return the images side by side
            matched_img = cv2.hconcat([gray1, gray2])

        return matched_img

    @output
    @render.ui
    def visualise_matched_fingerprints():
        if input.individualA() is None or input.individualB() is None:
            return ui.p("Please select both images.")

        matched_img = compare_matched_fingerprints()
        if matched_img is None:
            return ui.p("Error processing images.")

        matched_img_output = image_to_base64(matched_img)

        return ui.div(
            ui.h3(f"Fingerprint matching using {input.fingerprint()}"),
            ui.tags.img(
                src=f"data:image/png;base64,{matched_img_output}",
                style="max-width: 100%; height: auto;"
            )
        )
