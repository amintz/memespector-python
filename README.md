# memespector (python version)
Simple script for using Google Vision API. Ported and extended version of [bernorieder's memespector script](https://github.com/bernorieder/memespector).

It takes comma or tab-separated files containing a column with image URLs as inputs, sends images to the Vision API, parses the detected annotations and puts them back into the spreadsheet. Optionally, it also generates an image-label network which can be imported to Gephi.

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
4. In the same directory, create one folder named "data".
5. Place the input file in the "data" folder. It should be a comma- or tab-separated text file with one column containing URLs for the *image files*.
6. Rename config_sample.ini to config.ini and edit the settings according to your use of the script (see section below)

## Configuration
The config file contains several options which are all described in its comments. Below are the *mandatory* configurations. All the rest can be left with the default values for most use cases.
1. Project
    1. ProjectFolder: should be set to a meaningful name that describes your dataset. It will be used to create a folder bundling the output files.
2. InputConfiguration
    1. InputFile: should be set for the name of the comma- or tab-separated file placed in the "data" folder (Installation step 4)
    2. ImagesColumn: column header in the input file for the image URL addresses. Header must be unique.
    3. LinkColumn: column header in the input file for the URL of originating post or page. Header must be unique. It will be used as an attribute in the generated network.
    4. Delimiter: the character used in the input file to separate the columns. Use **\t** in case it is a tab-separated file and **,** in case it is a comma-separated file.
    5. Limit: number of rows of the file to be processed. Set 0 to process all.
3. ApiRequestFeatures
    1. Module list: set to 'yes' each of the Vision API modules you would like to enable in the requests.
    2. MaxResults: limits the number of results fetched from Vision API for each of the enabled modules. Set to 0 to not set the maximum, to which the Vision API will return the default maximum for each module.
    3. ApiKey: place the API key obtained from Google Cloud here (Installation step 1)

## Execution
Run the script "main.py" in a terminal window. To run in terminal, move to the script's directory and type
```
python main.py
```
If you have more than one python version installed, it might be needed to call python3 instead of python.
Check the terminal for possible errors and for progress reporting.

Terminal scripts can be interrupted by pressing Ctrl+C.

## Credits
Original memespector script by Bernhard Rieder. Ported to Python and extended by André Mintz. Feb 2018.

## Disclaimer
**As-is software, no support or warranty provided.**
