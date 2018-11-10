# memespector (python version)
Simple script for using Google Vision API. Ported and extended version of [bernorieder's memespector script](https://github.com/bernorieder/memespector).

Its purpose is batch processing images through Google Vision API. It takes as input primarily comma or tab-separated files containing a column with image URLs as inputs. It may also process folders containing images.

Each image is sent Google Vision API, the response is parsed and annotations are put in a new tabular file. It also generates a graph file for a bipartite image-label network, which can be imported to Gephi and plotted with [image network plotter](https://github.com/amintz/image-network-plotter) script.

Google Vision API modules currently supported:
* Label detection
* Explicit content detection
* Optical Character recognition
* Face detection
* Web detection

## Requirements
* Python 3 (Python 2 not supported)
* Python modules 'requests' and 'networkx'.

## Installation
1. Go to (http://apis.google.com), create an account, assign a payment method, enable Vision API and get an API Key. **Note that this is a paid service provided by Google, which can generate significant costs, use at your own risk.**
2. Download the script from this page, unzip and place the script files in some directory.
3. Install module requirements using pip. From terminal, go to the script's folder and call:
```
pip install -r requirements.txt
```
If you have more than one version of python installed, you may need to call pip for python3:
```
python3 -m pip install -r requirements.txt
```
or
```
pip3 install -r requirements.txt
```
4. Rename config_sample.txt to config.txt and edit the settings according to your use of the script (see section below).

## Configuration
The config file contains several options which are all described in its comments. Below are the *mandatory* configurations. All the rest can be left with the default values for most use cases.
1. Input configuration
    1. Input: *absolute path* of either the tabular file (comma- or tab-separated) containing the references to the images to be processed, or of the folder containing the images.
    2. ImagesColumn: in case the input is a tabular file, this should indicate the unique column header in the file for the column containing image references - these can be URLs or file names, in case the images are local.
    3. Delimiter: in case the input is a tabular file, the character used in the input file to separate the columns. Use **\t** in case it is a tab-separated file and **,** in case it is a comma-separated file.
    4. Limit: number of rows of the file to be processed. Set small limits to test the script, set to 0 to process all.
3. Api setup
    1. ApiKey: place the API key obtained from Google Cloud here (Installation step 1)
    2. Module list: set to 'yes' each of the Vision API modules you would like to enable in the requests.
    3. MaxResults: limits the number of results fetched from Vision API for each of the enabled modules. In case it is set to 0, this parameter will not be set, in which case the Vision API will return the default maximum for each module.

## Execution
Run the script "main.py" in a terminal window. To run in terminal, move to the script's directory and type
```
python memespector.py
```
or, depending on how your Python is installed
```
python3 memespector.py
```
Check the terminal for possible errors and for progress reporting.

Terminal scripts can be interrupted by pressing Ctrl+C.

## Credits
Original memespector script by Bernhard Rieder. Ported to Python and extended by André Mintz. Feb 2018.

## Disclaimer
**As-is software, no support or warranty provided.**
