# PlanarID

Many animals have characteristic colour patterns and markings that vary amongst individuals. PlanarID is a browser-based 
shiny app and collection of python pipeline scripts that facilitate individual recognition from photographs, leveraging 
unique, discrete colour markings on small, hard-bodied insects and other invertebrates.

This system is intended to work with animals that can be handled and photographed in a consistent manner. This pipeline 
uses colour-based thresholding techniques to split images into regions of pattern and not pattern before calculating some
meaningful _fingerprint_ for an individual. As such, animals with discrete colour patterns (e.g., bold stripes, obvious 
wing veining, or ink-blot style blobs) are its intended focus. Animals with diffuse patterns where colours or pattern 
regions fade into each other rather than having hard borders may still be analysed with this set-up, but performance may
be poor.

## Contents

- Getting started guide (below)
- [Tutorial and worked examples](tutorial/tutorial.md)
- [GUI overview](GUI%20overview.md)
- [Photography best practices](Photography%20best%20practices.md)
- [Photo-recapture - An explainer](Photographic%20datasets%20and%20mark-recapture%20-%20explained.md)
- Algorithm availability (below)
- Upgrade path (below)

<br>

## Getting started with PlanarID
I recommend installing an IDE (Pycharm Community Edition, Spyder, etc.) and [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
and cloning this repository. 

<table>
  <tr>
    <td align="left">
      <a href="https://www.jetbrains.com/pycharm/download/?section=windows" target="_blank">
        <img src="https://upload.wikimedia.org/wikipedia/commons/b/b2/PyCharm_Logo.jpg" width="50%">
      </a>
    </td>
    <td align="left">
      <a href="https://www.spyder-ide.org/" target="_blank">
        <img src="https://upload.wikimedia.org/wikipedia/commons/7/7e/Spyder_logo.svg" width="50%">
      </a>
    </td>
  </tr>
</table>

These scripts have been tested using Python 3.9 and Python 3.12, on both Ubuntu 22.04 and Windows 11. 
However, development was mainly conducted on a Linux machine; for best performance, Linux is preferred!  

<br>

### Downloading Planar-ID files

On launching your chosen IDE,this repository can be cloned with Git using the repo url (https://github.com/KynanDelaney/PlanarID.git).
A Python interpreter may need to be configured (i.e., telling your IDE program where which version of Python to use). Most 
IDEs will also suggest setting up a virtual environment, which is recommended.

<br>

### Installing packages and project setup

Once cloned, limited use should be immediately available by running the following commands in the console of your chosen IDE:

```bash
pip install -r requirements.txt
python project_folder_setup.py
```

This will install the necessary Python libraries, and, by default, create a working folder called "Tutorial" in the 
`/Documents` directory (structure outlined below.

<br>

### Launching the app
The browser-based shiny UI is launched from the terminal with the following:

```bash
shiny run planar-id.py
```

By default, this will connect with the existing "Tutorial" project directory. On linux, the app dashboard should launch 
automatically; on Windows, the user may need to navigate to the app in a web browser.

On both systems, the following code will be printed in the terminal - click on the `http` link, or copy it into your web 
browser to view and interact with the app:

```bash
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

To close the app, click on the console and hit CTRL+C to quit.

By default, the code snippets above will produce a new project folder (outline below) in `/Documents` called "Tutorial", 
and launch the shiny GUI that connects with default user parameters and visualisation/processing tools. For more guidance, 
example photos and corresponding tutorial are available in the `tutorial` folder of this repo.

<br>

## General details
To customise project names, one need only change the project name defined at the start of the `project_folder_setup.py`
and `planar-id.py` scripts to the desired name. This facilitates moving between several projects with minimal conflict.

<br>

General folder structure of active projects - produced by `project_folder_setup.py`:

```
[Project name]
|
|───unprocessed_photos
|
|───fingerprints
|
|───data  
|       user_parameters.csv
|       focal_df_template.csv
|
|───processing_errors
|       |───crop_rotate_size
|       |───crop_rotate_generic
|       └───fingerprinting
| 
|───logs
|       processing_error_logs.txt
|       fingerprinting_error_logs.txt
|       matching_error_logs.txt
|       processing_times.txt
|  
|───temp
|  
└───scripts
```

<br>

Initial (preferrably colour-corrected) images should be deposited in the `unprocessed_photos` folder. The `Photography best
practices` markdown file contains information on suitable methods of image capture and handling. Many app functions
rely on calling images and files from known locations - each function by default calls from and deposits into the relevant
locations without user intervention (outlined below).

<br>


## Availability of computer vision algorithms
AKAZE, ORB, and SIFT are freely-available computer-vision algorithms bundled with `opencv` in Python.
SURF, however, is under a [non-commercial licence](https://people.ee.ethz.ch/~surf/download.html) and not bundled with the default `opencv` library.
To enable SURF, `opencv` needs to be compiled with "non-free" algorithms enabled. 
We have had mixed success with this on Windows but [this page](https://www.samontab.com/web/2023/02/installing-opencv-4-7-0-in-ubuntu-22-04-lts/) outlines how to achieve this on Linux.

AKAZE, ORB, and SIFT are very effective at generating _fingerprints_ for comparison, so little is lost if SURF is not 
available to you. Further, the shiny GUI and pipeline will only present algorithms that are available to you, so an 
absence of SURF will not lead to errors or poor performance.

<br>

## Upgrade path

The current version of PlanarID is an effective tool for identifying individuals on the basis of unique, binary, colour-based
patterns. Future focuses for development are quality of life improvements for the UI, and methodological improvements for
the pipeline.

Core functions:
- Expand image processing to extract and process multiple colour ranges simultaneously.
- Add additional fingerprinting algorithms/ alternative fingerprint comparison methods.
- Add user control over settings for parallel processes (for RAM-limited computers).
- Configure available filtering values when generating pairwise lists.

<br>

Quality of life:
- Tooltips for all features requiring user interaction or decision-making.
- Enable user control over multiple or single matches allowed in `Individual Matching` page.
- More flexible within-individual quality control method to handle matched images from the end-stage of the pipeline.
- Better handling of `.csv`, output files, and parameter settings.
- Automate batch-processing steps (bundle `Crop and rotate`, `Extract fingerprints`, `Generate pairwise list`, and 
`Pairwise comparisons` together).
- Format and distribute PlanarID as a python package.