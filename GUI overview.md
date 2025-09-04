# GUI Overview
The browser-based GUI should open to a home page with details about the current contents of the project directory and 
various subfolders (Fig. 1). There is also a table of user-editable values for all stages of processing.

The "Naive Assessment" at the bottom of the page indicates the maximum number of pairwise comparisons possible in a dataset
of N images using the formula (N*(N-1))/2. Large photographic datasets (> 10,000 images) will quickly result in absurd 
numbers of potential comparisons (N<sub>10,000</sub> = 49,995,000 potential comparisons). In practice, filtering allowable
comparisons by date of capture, body size, or sex, reduces actual comparisons to more reasonable levels.

<br>

<p align="center" >
  <img src="readme_media/PlanarID_homepage.png" width="75%" style="border: 1px solid #005F6B; padding: 5px;">
  <figcaption align="center">Fig. 1: An example of the PlanarID homepage, outlining all user-definable parameters, details
about the photographic record and processing status, and ancillary information.</figcaption>
</p>

<br>

<br>

The user can navigate the different pages of the UI by clicking on the desired page in the top navbar. 
The **Image Processing** page (Fig. 2) and **Visualise Fingerprint Matching** page (Fig. 3) are interactive testing tools 
for the user to set and change all possible processing values on chosen images and pairs of images. The **Image Processing** 
page can access images anywhere on the machine, but **Visualise Fingerprint Matching** can only access images in the 
`unprocessed_photos` folder.

<br>

<p align="center">
  <img src="readme_media/PlanarID_image_processing.png" width="75%" style="border: 1px solid #005F6B; padding: 5px;">
  <figcaption align="center">Fig. 2: An interactive tool for changing image-processing settings. The original image (left)
is reduced in complexity to a discretized pattern (right). The consequences of these decisions on image segmentation and
"fingerprint" extraction are live-rendered</figcaption>
</p>

<br>

<p align="center">
  <img src="readme_media/PlanarID_visualise_fingerprint_matching.png" width="75%" style="border: 1px solid #005F6B; padding: 5px;">
  <figcaption align="center">Fig. 3: This tool allows the user to choose any pair of unprocessed images in the unprocessed_photos
folder, and visualise the quality of image segmentation and image comparison that emerges from settings defined in the previous
section.</figcaption>
</p>

<br>

<br>


The **Batch Processing** page is where the main functions of the pipeline can be called - segmenting images, extracting
fingerprints en-masse, generating a list of which images should be compared with each other, and running those pairwise
comparisons (Fig. 4). There is also a convenience tool that runs within-individual comparisons using selected fingerprints to help
spot mis-labelled, blurred, or otherwise problematic images.

<br>

<p align="center">
  <img src="readme_media/PlanarID_batch_processing.png" width="75%" style="border: 1px solid #005F6B; padding: 5px;">
  <figcaption align="center">Fig. 4: The work-centre of the PlanarID app: all stages of image processing and comparison
are launched from this window. Settings defined in the interactive tools (above) are applied to hundreds, thousands, or tens 
of thousands of images and extracted patterns.</figcaption>
</p>

<br>

<br>

The **Individual Matching** page takes the output of pairwise comparisons (a `.csv` file) and shows these results to the 
user, with buttons for navigating, choosing which _fingerprinting_ algorithm to sort by,and confirming matches in the 
photographic record.

<br>

<p align="center">
  <img src="readme_media/PlanarID_individual_matching.png" width="75%" style="border: 1px solid #005F6B; padding: 5px;">
  <figcaption align="center">Fig. 5: The final step of identifying individuals that were recaptured. The user selects
a csv outputted from "Run Pairwise Comparisons" and manually compares a chosen number of best-matching options for each
focal individual according to 1 of 4 algorithms at a time. The presence or absence of a matching image is confirmed and 
written to a results .csv. </figcaption>
</p>

<br>

<br>

The **Generate and Visualise Encounter History** page is a convenience tool for converting the output of confirmed matches
(`matches_YYYY_MM_DD.csv`) into a census-style encounter history. This tool renders tables of encounter frequencies per
individual identified in the photographic record, and a population-level distribution of encounter frequencies (Figure 6). 
Saving the census-style history makes the output of PlanarID more readily usable by mark-recapture packages in R, but is 
not strictly necessary! 

The network graph can be used as a diagnostic tool for the matching output (or just looks nice!). Chains of matched images
should be clear and disconnected from other chains. If there are erroneous matches, these may be apparent as two distinct
chains of images connected by a single node - this should prompt some investigation into that collection of images.


<p align="center">
  <img src="readme_media/PlanarID_generate_and_visualise_encounter_history.png" width="75%" style="border: 1px solid #005F6B; padding: 5px;">
  <figcaption align="center">Fig. 6: A convenience tool for summarising and saving the capture record in an accessible format.
The user selects a "matches" csv outputted from the "Individual matching" process. </figcaption>
</p>

<br>

<br>

The **Within-Individual Quality Control** page takes the output of within-individual comparisons (a `.csv` file) and shows
network graphs of apparent within-individual dissimilarity and a gallery of all images of the chosen individual (Fig. 7).

<br>

<p align="center">
  <img src="readme_media/PlanarID_quality_control.png" width="75%" style="border: 1px solid #005F6B; padding: 5px;">
  <figcaption align="center">Fig. 7: A network graph of within-individual photographic example similarity and a gallery 
of relevant images for quality-control. In the graph, correctly named images (ascribed to the right individual) should form
a cluster, and obvious outliers will be removed from that cluster.</figcaption>
</p>

<br>

<br>


<br>

## Core app processes and values

There are many settings of colour thresholds, image blurring, and _fingerprint_ sensitivity to obvious or subtle marks. 
Some key details of these parameters, their consequences, and use are outlined below.

<br>

### Splitting images into _pattern_ and _not pattern_
This involves taking high quality and/or colour-corrected images and using colour thresholding (Figure 2;8) to extract regions of the
_pattern_. The process can be visualised in the shiny UI and all possible values played with. When suitable values have 
been chosen, this process can be applied at scale. This step results in a cropped version of the original image and a 
_mask_ (a twin image containing only the pattern, with other details blacked out).

| Parameter       | Meaning/Consequence                                                                                                              |                                                          Possible Values |
|:----------------|:---------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------:|
| hue_low         | The lower bound of colour (i.e., red, burnt-orange, yellow or blue, etc.) on which images are segmented                          |                                                Integer between 0 and 179 |
| saturation_low  | The lower bound of colour vibrance or intensity (i.e., grey, pastel, or intense colour) on which images are segmented            |                                                Integer between 0 and 255 | 
| value_low       | The lower bound of brightness (i.e., from very dark/black through to white) on which images are segmented                        |                                                Integer between 0 and 255 |
| hue_high        | The upper bound of colour (i.e., red, burnt-orange, yellow or blue, etc.) on which images are segmented                          |                                                Integer between 0 and 179 |
| saturation_high | The upper bound of colour vibrance or intensity (i.e., grey, pastel, or intense colour) on which images are segmented            |                                                Integer between 0 and 255 | 
| value_high      | The upper bound of brightness (i.e., from very dark/black through to white) on which images are segmented                        |                                                Integer between 0 and 255 |
| kernel_size     | The amount of smoothing applied to the border of _pattern_ and _not pattern_ areas of images                                     |                                      Odd integer >= 1 (e.g., 1,3,5,7...) |
| threshold_value | A grey-scale threshold for accepting/rejecting regions of images as parts of the identifying _pattern_                           |                                                Integer between 0 and 255 |
| num_patches     | The number of identifying marks/ colour-patches expected from a single individual                                                |       Depending on the idiosyncracies of the study species; Integer >= 1 |
| min_area        | The minimum expected area (in pixels) of each identifying mark/ colour-patch. Used to filter out dirt, noise or visual artefacts |  Depending on the magnification and resolution of images; Integer >= 100 |
| mult            | A scalar indicating how much area around the identifying pattern should be included in processed masks and images                |                                                               Float >= 1 |
| cutoff_size     | The total size (in pixels) a correctly-processed image should be, after colour-based segmentation and cropping                   | Depending on the magnification and resolution of images; Integer >= 100  |

<br>

<table>
  <tr>
    <td align="center"><img src="readme_media/colour_space_plot.png" height="75%"><br><sub>H[0:179] S[0:255] V[0:255]</sub></td>
    <td align="center"><img src="readme_media/filtered_colour_space_plot.png" height="75%"><br><sub> H[11:40] S[75:240] V[80:240]</sub></td>
  </tr>
</table>
<p align="center"><em>Figure 8: The full HSV colour space and an example of filtering the HSV space to a range of values, 
as in our colour-thresholding.</em></p>


<br>

### Extracting _fingerprints_ from processed images
This involves processing _masks_ of each individuals' _pattern_ and calculating keypoints and descriptors that describe 
large areas of _pattern_, turning points, colour gradients, and corners.
These _fingerprints_ are saved as `.txt` files for later use.
Four algorithms (available for non-commercial use) are available - AKAZE, ORB, SIFT, and SURF (see more below).

| Parameter          | Meaning/Consequence                                                                                           |               Possible Values |
|:-------------------|:--------------------------------------------------------------------------------------------------------------|------------------------------:|
| hessian_threshold  | A value used by the SURF algorithm to filter out non-meaningful keypoints. Larger values are more selective.  |              Integer >= 100   |
| akaze_threshold    | A value used by the AKAZE algorithm to filter out non-meaningful keypoints. Larger values are more selective. | Float between 0.0001 and 0.01 |
| n_features         | The maximum number of keypoints to be extracted from _patterns_ by SIFT and ORB                               |                Integer >= 100 |

<br>

### Generating list of pairwise comparisons to run
This stage involves providing a `.csv` of focal individuals (i.e., individuals in the photographic record you want to 
identify) and a `.csv` of a test individuals (i.e., the bank of photographed individuals you want to compare against).
These `.csv` files can be identical, partially overlapping, or non-overlapping, depending on when data were collected 
and which individuals you wish to focus on. A template of appropriate format is generated when the project folder is created.
This function compares the focal and test set of individuals by (optionally) size, sex, and date to identify which individuals
could reasonably be compared based solely on this metadata. Date and sex filters are chosen interactively in the UI, 
while accepted error in body size is a saved parameter (below).

| Parameter    | Meaning/Consequence                                                                                                |                                                     Possible Values |
|:-------------|:-------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------:|
| size_offset  | The amount of error +/- an individuals' body size that will be accepted as an appropriate candidate for comparison |  Depending on the chosen body size/weight measure chosen; Float > 0 |

<br>

### Conducting pairwise comparisons

This stage takes the output of the previous step (a `.csv` file) and conducts the appropriate comparisons. A _distance_ value 
is generated for each pairwise comparison according to one or more of four _fingerprint_ algorithms. A large _distance_ means 
two images/patterns are very dissimilar and thus unlikely to contain the same individual, while small _distances_ indicate 
two images/fingerprints are very similar and thus potentially are images of the same individual at two points in time. 
This produces two `.csv` files - the complete output of all pairwise comparisons and their _distance_ values (potentially 
millions of rows long), and a filtered subset that contains the N best matches for each focal individual according to all
chosen algorithms (a smaller, more manageable file). This second, filtered file is used in the ***Individual Matching*** page.


| Parameter                     | Meaning/Consequence                                                                                                                         |          Possible Values |
|:------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------|-------------------------:|
| number_comparisons_considered | The number of _N_ best matches for each focal individual according to all chosen algorithms that the pairwise results should be filtered to | Integer between 1 and 40 |

<br>