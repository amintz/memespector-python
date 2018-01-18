import configparser, requests, csv, json, os, sys, itertools, hashlib, re
import functions as f
import googleconnect as gapi
from shutil import copyfile

sys.tracebacklimit = 0

settings = configparser.ConfigParser()
settings._interpolation = configparser.ExtendedInterpolation()
settings.read('config.ini')

print("\n-------------------------\nMemespector Python script\n-------------------------")

# ------------------------------------------
# Create folders
#-------------------------------------------

dir_path        = os.path.dirname(os.path.realpath(__file__))
dataFolder      = dir_path + '/' + settings['Folders']['DataFolder']
cacheFolder     = dir_path + '/' + settings['Folders']['CacheFolder']
outputsFolder   = dir_path + '/' + settings['Folders']['OutputsFolder']
imageCpFolder   = dir_path + '/' + settings['Folders']['ImageCopyFolder']
cacheCopyFolder = dir_path + '/' + settings['Folders']['CacheCopyFolder']

if not os.path.exists(cacheFolder):
    os.makedirs(cacheFolder)

if os.path.exists(outputsFolder):
    answer = input("\nATTENTION: Project folder already exists. There is risk of overwriting files. Continue? Y or N > ")
    if answer.lower() == 'n':
        sys.exit()
else:
    os.makedirs(outputsFolder)

if not os.path.exists(imageCpFolder):
    os.makedirs(imageCpFolder)

if not os.path.exists(cacheCopyFolder):
    os.makedirs(cacheCopyFolder)

# ------------------------------------------
# Configure Processing attributes
# ------------------------------------------

gapi.printModuleConfiguration()

imagesRemote = f.yn(settings['SourceImagesLocation']['ImagesRemote'])
absolutePath = f.yn(settings['SourceImagesLocation']['AbsolutePath'])
forceBase64 = f.yn(settings['SourceImagesLocation']['ForceBase64'])
saveImageCopy = f.yn(settings['SourceImagesLocation']['SaveImageCopy'])
inputImageFolder = settings['SourceImagesLocation']['InputImageFolder']

print("HANDLING OF IMAGE SOURCE\n")
if imagesRemote:
    print("\tOnline images")
    if forceBase64:
        print("\tLocal intermediation of data submission (forcing base64)")
    else:
        print("\tRemotely retrieved by Google")
    if saveImageCopy:
        print("\tSaving local copies of processed images")
    else:
        print("\tNot saving local copies")
else:
    print("\tProcessing local images")
    if absolutePath:
        print("\tReading file paths as absolute")
    else:
        print("\tReading file paths as relative to: " + inputImageFolder)
print()

# ------------------------------------------
# Get input
# ------------------------------------------

inputFileName = settings['InputConfiguration']['InputFile']
inputFilePath = dataFolder + inputFileName

try:
    inputFile = open(inputFilePath)
except Exception:
    sys.exit('\n**ERROR**\nInput file could not be opened. Please check the configuration file.\n')

csvDialect = csv.Sniffer().sniff(inputFile.read(1024))
csvDialect.escapechar = "\\"
delimiter = settings['InputConfiguration']['Delimiter'].encode('utf-8').decode('unicode_escape')

print("Delimiter: " + delimiter)

csvDialect.delimiter = delimiter

inputFile.seek(0)
inputCSV = csv.reader(inputFile, csvDialect)
inputHeader = next(inputCSV)

imagesColumn = settings['InputConfiguration']['ImagesColumn']

if imagesColumn in inputHeader:
    imagesColumnIdx = inputHeader.index(imagesColumn)
else:
    print(inputHeader)
    sys.exit('\n**ERROR**\nImage column could not be found in input file. Please check the configuration file.\n')

# Workaround for Facebook URLs messing with filename extensions
if ("created_time_unix" in inputHeader) or  ("post_published_unix" in inputHeader):
    isFacebook = True
else:
    isFacebook = False

numImages = sum(1 for row in inputCSV)
inputFile.seek(0)

procLimit = int(settings['InputConfiguration']['Limit'])

if procLimit > numImages or procLimit == 0:
    procLimit = numImages

print("DATA FILE\n")
print("\tSource file path\n\t\t" + inputFilePath)
print("\tNumber of entries\n\t\t" + str(numImages))
print("\tProcessing limit\n\t\t" + str(procLimit))
print("\tImage column header\n\t\t" + imagesColumn + "(" + str(imagesColumnIdx) + ")")
print("\n-------------------------")
# ------------------------------------------
# Create output file
# ------------------------------------------

outputFileName = "processed_" + inputFileName
outputFilePath = outputsFolder + outputFileName

try:
    outputFile = open(outputFilePath, 'w', newline='')
except Exception:
    sys.exit('\n**ERROR**\nOutput file could not be created. Please check the configuration file.\n')

outputCSV = csv.writer(outputFile, csvDialect)

# Add columns to input file
outputHeader = inputHeader + ['original_filename', 'image_id', 'file_ext', 'copy_filename', 'gv_ss_adult','gv_ss_spoof','gv_ss_medical','gv_ss_violence','gv_labels', 'gv_text', 'gv_text_lang', 'gv_web_entities', 'gv_web_full_matching_images', 'gv_web_partial_matching_images', 'gv_web_pages_with_matching_images', 'gv_web_visually_similar_images', 'gv_num_faces', 'gv_face_joy', 'gv_face_sorrow', 'gv_face_anger', 'gv_face_surprise']

outputCSV.writerow(outputHeader)

# ------------------------------------------
# Process images
# ------------------------------------------

next(inputCSV)

for i in range(procLimit):

    print("\nImage %s of %s" % (i+1, procLimit))

    inputRow = next(inputCSV)
    outputRow = inputRow

    # Retrieve image path from input
    imagePath = inputRow[imagesColumnIdx]

    # If image is local and path is not absolute, make up absolute path
    if not imagesRemote and not absolutePath:
        imagePath = inputImageFolder + imagePath

    # Clean file name and extension from path if Facebook data
    if isFacebook:
        originalFileName = os.path.basename(re.findall(".+\/(.+?)\?", imagePath)[0])
    else:
        originalFileName = os.path.basename(imagePath)

    extension = os.path.splitext(originalFileName)[1]

    # Create hash for image url
    hashObj = hashlib.sha1(imagePath.encode('utf-8'))
    imageHash = hashObj.hexdigest()

    # Make image copy
    copyFilename = imageHash + extension
    if(saveImageCopy):
        copyFilePath = imageCpFolder + copyFilename
        if not os.path.isfile(copyFilePath):
            print("\tCopying image...", end="")
            try:
                image = requests.get(imagePath, allow_redirects=True)
            except Exception:
                sys.exit('\n**ERROR**\nCould not retrieve remote image. Check data, internet connection, configuration.\n')
            open(copyFilePath,"wb").write(image.content)
            print("done")
        else:
            print("\tCopy already existed")

    # Process image

    responseFile = cacheFolder + imageHash + '.json'
    responseFileCp = cacheCopyFolder + imageHash + '.json'

    if not (os.path.isfile(responseFile)):
        if imagesRemote and forceBase64 and saveImageCopy:
            # If images are remote but are to be processed through local base64 coding and copies have been made, use copies for network traffic efficiency.
            responseData = gapi.processImage(copyFilePath, remote=False)
            if not responseData:
                continue
        else:
            responseData = gapi.processImage(imagePath)
            if not responseData:
                continue
        with open(responseFile, 'w') as outFile:
            json.dump(responseData, outFile, indent=4, sort_keys=True)
        copyfile(responseFile, responseFileCp)

    else:
        print("\t*ATTENTION* Using cached content (remove all files in the cache folder if you see this message and the tool is not working yet)")
        copyfile(responseFile, responseFileCp)
        responseData = json.load(open(responseFile))

    # Parse API response

    # Safe Search
    if 'safeSearchAnnotation' in responseData['responses'][0]:
        gv_ss_adult = responseData['responses'][0]['safeSearchAnnotation']['adult']
        gv_ss_spoof = responseData['responses'][0]['safeSearchAnnotation']['spoof']
        gv_ss_medical = responseData['responses'][0]['safeSearchAnnotation']['medical']
        gv_ss_violence = responseData['responses'][0]['safeSearchAnnotation']['violence']
    else:
        gv_ss_adult = "NONE"
        gv_ss_spoof = "NONE"
        gv_ss_medical = "NONE"
        gv_ss_violence = "NONE"

    # Labels
    if 'labelAnnotations' in responseData['responses'][0]:
        gv_labels = []
        for label in responseData['responses'][0]['labelAnnotations']:
            gv_labels.append(label['description'] + "(" + str(label['score']) + ")")
        gv_labels = ",".join(gv_labels)
    else:
        gv_labels = "NONE"

    # Text
    if 'textAnnotations' in responseData['responses'][0]:
        gv_text = responseData['responses'][0]['textAnnotations'][0]['description']
        gv_text = re.sub("[\n\t\r]", " ", gv_text)
        gv_text_lang = responseData['responses'][0]['textAnnotations'][0]['locale']
    else:
        gv_text = "NONE"
        gv_text_lang = "NONE"

    # Web Detection
    if 'webDetection' in responseData['responses'][0]:
        if 'fullMatchingImages' in responseData['responses'][0]['webDetection']:
            gv_web_full_matching_images = []
            for url in responseData['responses'][0]['webDetection']['fullMatchingImages']:
                gv_web_full_matching_images.append(url['url'].replace(",", "%2C"))
            gv_web_full_matching_images = ",".join(gv_web_full_matching_images)
        else:
            gv_web_full_matching_images = "NONE"
        if 'pagesWithMatchingImages' in responseData['responses'][0]['webDetection']:
            gv_web_pages_with_matching_images = []
            for url in responseData['responses'][0]['webDetection']['pagesWithMatchingImages']:
                gv_web_pages_with_matching_images.append(url['url'].replace(",", "%2C"))
            gv_web_pages_with_matching_images = ",".join(gv_web_pages_with_matching_images)
        else:
            gv_web_pages_with_matching_images = "NONE"
        if 'partialMatchingImages' in responseData['responses'][0]['webDetection']:
            gv_web_partial_matching_images = []
            for url in responseData['responses'][0]['webDetection']['partialMatchingImages']:
                gv_web_partial_matching_images.append(url['url'].replace(",", "%2C"))
            gv_web_partial_matching_images = ",".join(gv_web_partial_matching_images)
        else:
            gv_web_partial_matching_images = "NONE"
        if 'visuallySimilarImages' in responseData['responses'][0]['webDetection']:
            gv_web_visually_similar_images = []
            for url in responseData['responses'][0]['webDetection']['visuallySimilarImages']:
                gv_web_visually_similar_images.append(url['url'].replace(",", "%2C"))
            gv_web_visually_similar_images = ",".join(gv_web_visually_similar_images)
        else:
            gv_web_visually_similar_images = "NONE"
        if 'webEntities' in responseData['responses'][0]['webDetection']:
            gv_web_entities = []
            for entity in responseData['responses'][0]['webDetection']['webEntities']:
                if 'description' in entity:
                    description = entity['description']
                else:
                    description = "NONE"
                gv_web_entities.append(description + "(" + str(entity['score']) + ")")
            gv_web_entities = ",".join(gv_web_entities)
        else:
            gv_web_entities = "NONE"
    else:
        gv_web_full_matching_images = "NONE"
        gv_web_pages_with_matching_images = "NONE"
        gv_web_partial_matching_images = "NONE"
        gv_web_visually_similar_images = "NONE"
        gv_web_entities = "NONE"

    # Face
    if 'faceAnnotations' in responseData['responses'][0]:
        gv_num_faces = 0;
        gv_face_joy = 'VERY_UNLIKELY'
        gv_face_sorrow = 'VERY_UNLIKELY'
        gv_face_anger = 'VERY_UNLIKELY'
        gv_face_surprise = 'VERY_UNLIKELY'
        for face in responseData['responses'][0]['faceAnnotations']:
            gv_face_joy = f.likelihoodCompare(gv_face_joy, face['joyLikelihood'])
            gv_face_sorrow = f.likelihoodCompare(gv_face_sorrow, face['sorrowLikelihood'])
            gv_face_anger = f.likelihoodCompare(gv_face_anger, face['angerLikelihood'])
            gv_face_surprise = f.likelihoodCompare(gv_face_surprise, face['surpriseLikelihood'])
            gv_num_faces +=1
    else:
        gv_face_joy = 'NONE'
        gv_face_sorrow = 'NONE'
        gv_face_anger = 'NONE'
        gv_face_surprise = 'NONE'
        gv_num_faces = '0'

    # Add values to output row
    outputRow.append(originalFileName)
    outputRow.append(imageHash)
    outputRow.append(extension)
    outputRow.append(copyFilename)
    outputRow.append(gv_ss_adult)
    outputRow.append(gv_ss_spoof)
    outputRow.append(gv_ss_medical)
    outputRow.append(gv_ss_violence)
    outputRow.append(gv_labels)
    outputRow.append(gv_text)
    outputRow.append(gv_text_lang)
    outputRow.append(gv_web_entities)
    outputRow.append(gv_web_full_matching_images)
    outputRow.append(gv_web_partial_matching_images)
    outputRow.append(gv_web_pages_with_matching_images)
    outputRow.append(gv_web_visually_similar_images)
    outputRow.append(gv_num_faces)
    outputRow.append(gv_face_joy)
    outputRow.append(gv_face_sorrow)
    outputRow.append(gv_face_anger)
    outputRow.append(gv_face_surprise)

    # Write results to output file
    outputCSV.writerow(outputRow)
