import configparser, requests, csv, json, os, sys, itertools, hashlib, re, platform, traceback
from shutil import copyfile
import networkx as nx
import functions as f
from visionapirequest import VisionApiRequest

def main():
    try:
        # ------------------------------------------
        # Platform check
        #-------------------------------------------

        sys.tracebacklimit = 0

        if platform.system() == 'Windows':
            iswindows = True
            slash = '\\'
        else:
            iswindows = False
            slash = '/'

        # ------------------------------------------
        # Read the config file
        #-------------------------------------------

        settings = configparser.ConfigParser()
        settings._interpolation = configparser.ExtendedInterpolation()

        try:
            settings.read('config.ini')
        except Exception:
            sys.exit('\n**ERROR**\nCould not open configuration file. It should be in the same folder as the script and named \'config.ini\'\n')

        print("\n-------------------------\nMemespector Python script\n-------------------------")


        try:
            projectFolder     = settings['Project']['YourProjectFolder']

            dir_path        = os.path.dirname(os.path.realpath(__file__))
            dataFolder      = dir_path + slash + settings['Folders']['DataFolder'] + slash
            cacheFolder     = dir_path + slash + settings['Folders']['CacheFolder'] + slash
            outputsFolder   = dir_path + slash + settings['Folders']['OutputsFolder'] + slash + projectFolder + slash
            imageCpFolder   = outputsFolder + settings['Folders']['ImageCopyFolder'] + slash
            cacheCopyFolder = outputsFolder + settings['Folders']['CacheCopyFolder'] + slash

            makeNetwork = f.yn(settings['OutputConfiguration']['MakeNetwork'])

            imagesRemote = f.yn(settings['SourceImagesLocation']['ImagesRemote'])
            absolutePath = f.yn(settings['SourceImagesLocation']['AbsolutePath'])
            forceBase64 = f.yn(settings['SourceImagesLocation']['ForceBase64'])
            saveImageCopy = f.yn(settings['SourceImagesLocation']['SaveImageCopy'])
            inputImageFolder = settings['SourceImagesLocation']['InputImageFolder']

            labelThreshold = float(settings['OutputConfiguration']['LabelScoreFilter'])
            includeScore = f.yn(settings['OutputConfiguration']['IncludeScoreInSpreadsheet'])

            inputFileName = settings['InputConfiguration']['InputFile']
            inputFilePath = dataFolder + inputFileName
            delimiter = settings['InputConfiguration']['Delimiter'].encode('utf-8').decode('unicode_escape')

            imagesColumn = settings['InputConfiguration']['ImagesColumn']
            linkColumn = settings['InputConfiguration']['LinkColumn']
            if linkColumn=="":
                linkColumn = imagesColumn

            procLimit = int(settings['InputConfiguration']['Limit'])

            imagesRemote = f.yn(settings['SourceImagesLocation']['ImagesRemote'])
            forceBase64 = f.yn(settings['SourceImagesLocation']['ForceBase64'])

            labelDetection = f.yn(settings['ApiRequestFeatures']['Label']),
            safeSearchDetection = f.yn(settings['ApiRequestFeatures']['SafeSearch']),
            textDetection = f.yn(settings['ApiRequestFeatures']['Text']),
            webDetection = f.yn(settings['ApiRequestFeatures']['Web']),
            faceDetection = f.yn(settings['ApiRequestFeatures']['Face'])

            maxResults = settings['ApiRequestFeatures']['MaxResults']
            apiKey = settings['ApiRequestFeatures']['ApiKey']

            if maxResults == "0":
                setMaxResults = False
            else:
                setMaxResults = True

        except Exception:
            sys.exit("\n**ERROR**\nCould not parse at least one of the settings from the config file. Please verify its contents carefully.")

        # ------------------------------------------
        # Create folders
        #-------------------------------------------

        if not os.path.exists(cacheFolder):
            os.makedirs(cacheFolder)

        if os.path.exists(outputsFolder):
            answer = input("\nATTENTION: Project folder already exists. There is risk of overwriting files. Continue? Y or N > ")
            if answer.lower() == 'n':
                sys.exit('Rename project in config file.')
            elif answer.lower() == 'y':
                print('Continuing overwriting existing files.')
            else:
                sys.exit('Answer not understood. Exiting.')
        else:
            os.makedirs(outputsFolder)

        if not os.path.exists(imageCpFolder):
            os.makedirs(imageCpFolder)

        if not os.path.exists(cacheCopyFolder):
            os.makedirs(cacheCopyFolder)

        # ------------------------------------------
        # Configure Processing attributes
        # ------------------------------------------

        apirequest = VisionApiRequest(apiKey, setMaxResults, maxResults, labelDetection, safeSearchDetection, textDetection, webDetection, faceDetection)

        apirequest.printModuleConfiguration()

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

        try:
            inputFile = open(inputFilePath, encoding='utf8')
        except Exception:
            sys.exit('\n**ERROR**\nInput file could not be opened. Please check the configuration file.\n')

        print("Delimiter: " + delimiter)

        csvDialect = csv.Sniffer().sniff(inputFile.read(1024), delimiters=delimiter)

        if not csvDialect.escapechar:
            csvDialect.escapechar = "\\"
        print("Escape char: " + str(csvDialect.escapechar))

        inputFile.seek(0)
        inputCSV = csv.reader(inputFile, csvDialect)
        inputHeader = next(inputCSV)

        if imagesColumn in inputHeader:
            imagesColumnIdx = inputHeader.index(imagesColumn)
        else:
            print(inputHeader)
            sys.exit('\n**ERROR**\nImage column could not be found in input file. Please check the configuration file.\n')

        if makeNetwork:
            if linkColumn in inputHeader:
                linkColumnIdx = inputHeader.index(linkColumn)
            else:
                print(inputHeader)
                sys.exit('\n**ERROR**\nLink column could not be found in input file. Please check the configuration file\n')

        # Workaround for Facebook URLs messing with filename extensions
        if ("created_time_unix" in inputHeader) or  ("post_published_unix" in inputHeader):
            isFacebook = True
        else:
            isFacebook = False

        numImages = sum(1 for row in inputCSV)
        inputFile.seek(0)


        if procLimit > numImages or procLimit == 0:
            procLimit = numImages

        print("DATA FILE\n")
        print("\tSource file path\n\t\t" + inputFilePath)
        print("\tNumber of entries\n\t\t" + str(numImages))
        print("\tProcessing limit\n\t\t" + str(procLimit))
        print("\tImage column header\n\t\t" + imagesColumn + "(" + str(imagesColumnIdx) + ")")
        print("\n-------------------------")

        # ------------------------------------------
        # Create output files
        # ------------------------------------------

        outputFileName = "annotated_" + inputFileName
        outputFilePath = outputsFolder + outputFileName

        try:
            outputFile = open(outputFilePath, 'w', newline='', encoding='utf8')
        except Exception:
            sys.exit('\n**ERROR**\nOutput file could not be created. Please check the configuration file.\n')

        outputCSV = csv.writer(outputFile, csvDialect)

        # Add columns to input file
        outputHeader = inputHeader + ['original_filename', 'image_id', 'file_ext', 'copy_filename', 'gv_ss_adult','gv_ss_spoof','gv_ss_medical','gv_ss_violence','gv_labels', 'gv_text', 'gv_text_lang', 'gv_web_entities', 'gv_web_full_matching_images', 'gv_web_partial_matching_images', 'gv_web_pages_with_matching_images', 'gv_web_visually_similar_images', 'gv_num_faces', 'gv_face_joy', 'gv_face_sorrow', 'gv_face_anger', 'gv_face_surprise']

        outputCSV.writerow(outputHeader)

        if makeNetwork:
            graph = nx.Graph()
            graphfilename = "img-label-net_" + inputFileName.split(".")[0] + ".gexf"
            graphfilepath = outputsFolder + graphfilename
            foundlabels = []

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
            print("\tImage ID: %s" % (imageHash))

            # Make image copy
            copyFilename = imageHash + extension
            if(saveImageCopy):
                copyFilePath = imageCpFolder + copyFilename
                if not os.path.isfile(copyFilePath):
                    print("\tCopying image...", end="")
                    sys.stdout.flush()
                    try:
                        image = requests.get(imagePath, allow_redirects=True)
                    except Exception:
                        print('\n\t**ERROR**\n\tCould not retrieve remote image. Check data, internet connection, configuration.\n')
                        outputCSV.writerow(outputRow)
                        continue
                    open(copyFilePath,"wb").write(image.content)
                    print("done")
                else:
                    print("\tCopy already existed")

            if makeNetwork:
                nodelink = inputRow[linkColumnIdx]
                graph.add_node(imageHash, type='image', label='_image', file=copyFilename, link=nodelink)

            # Process image

            responseFile = cacheFolder + imageHash + '.json'
            responseFileCp = cacheCopyFolder + imageHash + '.json'

            if not (os.path.isfile(responseFile)):
                if imagesRemote and forceBase64 and saveImageCopy:
                    # If images are remote but are to be processed through local base64 coding and copies have been made, use copies for network traffic efficiency.
                    apirequest.annotateImage(copyFilePath, isRemote=False)
                    responseData = apirequest.getResponse()
                    if not responseData:
                        outputCSV.writerow(outputRow)
                        continue
                else:
                    apirequest.annotateImage(imagePath, isRemote=imagesRemote, base64Encode=forceBase64)
                    responseData = apirequest.getResponse()
                    if not responseData:
                        outputCSV.writerow(outputRow)
                        continue
                with open(responseFile, 'w', encoding='utf8') as outFile:
                    json.dump(responseData, outFile, indent=4, sort_keys=True)
                copyfile(responseFile, responseFileCp)

            else:
                print("\t*ATTENTION* Using cached content (remove all files in the cache folder if you see this message and the tool is not working yet)")
                copyfile(responseFile, responseFileCp)
                responseData = json.load(open(responseFile, encoding='utf8'))

            # Parse API response
            try:
                response = responseData['responses'][0]
            except Exception:
                print('\t*ATTENTION* Vision API returned an error for this image. Check JSON file for details.\n\tMoving on to next image.\n')
                outputCSV.writerow(outputRow)
                continue

            # Safe Search
            if 'safeSearchAnnotation' in response:
                gv_ss_adult = response['safeSearchAnnotation']['adult']
                gv_ss_spoof = response['safeSearchAnnotation']['spoof']
                gv_ss_medical = response['safeSearchAnnotation']['medical']
                gv_ss_violence = response['safeSearchAnnotation']['violence']
            else:
                gv_ss_adult = "NONE"
                gv_ss_spoof = "NONE"
                gv_ss_medical = "NONE"
                gv_ss_violence = "NONE"

            # Labels
            if 'labelAnnotations' in response:
                gv_labels = []
                for label in response['labelAnnotations']:
                    if label['score'] < labelThreshold:
                        continue;
                    if label['mid']=='':
                        label_id = "_" + label['description']
                    else:
                        label_id = label['mid']
                    if makeNetwork:
                        if not label_id in foundlabels:
                            foundlabels.append(label_id)
                            graph.add_node(label_id,type='gv_label', label=label['description'], mid=label['mid'], description=label['description'])
                        graph.add_edge(imageHash, label_id, score=label['score'], topicality=label['topicality'])
                    if includeScore:
                        gv_labels.append(label['description'] + "(" + str(label['score']) + ")")
                    else:
                        gv_labels.append(label['description'])
                gv_labels = ",".join(gv_labels)
            else:
                gv_labels = "NONE"

            # Text
            if 'textAnnotations' in response:
                gv_text = response['textAnnotations'][0]['description']
                gv_text = re.sub("[\n\t\r]", " ", gv_text)
                gv_text_lang = response['textAnnotations'][0]['locale']
            else:
                gv_text = "NONE"
                gv_text_lang = "NONE"

            # Web Detection
            if 'webDetection' in response:
                if 'fullMatchingImages' in response['webDetection']:
                    gv_web_full_matching_images = []
                    for url in response['webDetection']['fullMatchingImages']:
                        gv_web_full_matching_images.append(url['url'].replace(",", "%2C"))
                    gv_web_full_matching_images = ",".join(gv_web_full_matching_images)
                else:
                    gv_web_full_matching_images = "NONE"
                if 'pagesWithMatchingImages' in response['webDetection']:
                    gv_web_pages_with_matching_images = []
                    for url in response['webDetection']['pagesWithMatchingImages']:
                        gv_web_pages_with_matching_images.append(url['url'].replace(",", "%2C"))
                    gv_web_pages_with_matching_images = ",".join(gv_web_pages_with_matching_images)
                else:
                    gv_web_pages_with_matching_images = "NONE"
                if 'partialMatchingImages' in response['webDetection']:
                    gv_web_partial_matching_images = []
                    for url in response['webDetection']['partialMatchingImages']:
                        gv_web_partial_matching_images.append(url['url'].replace(",", "%2C"))
                    gv_web_partial_matching_images = ",".join(gv_web_partial_matching_images)
                else:
                    gv_web_partial_matching_images = "NONE"
                if 'visuallySimilarImages' in response['webDetection']:
                    gv_web_visually_similar_images = []
                    for url in response['webDetection']['visuallySimilarImages']:
                        gv_web_visually_similar_images.append(url['url'].replace(",", "%2C"))
                    gv_web_visually_similar_images = ",".join(gv_web_visually_similar_images)
                else:
                    gv_web_visually_similar_images = "NONE"
                if 'webEntities' in response['webDetection']:
                    gv_web_entities = []
                    for entity in response['webDetection']['webEntities']:
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
            if 'faceAnnotations' in response:
                gv_num_faces = 0;
                gv_face_joy = 'VERY_UNLIKELY'
                gv_face_sorrow = 'VERY_UNLIKELY'
                gv_face_anger = 'VERY_UNLIKELY'
                gv_face_surprise = 'VERY_UNLIKELY'
                for face in response['faceAnnotations']:
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
        if makeNetwork:
            nx.write_gexf(graph, graphfilepath)
    except KeyboardInterrupt:
        if makeNetwork:
            if graph:
                nx.write_gexf(graph,graphfilepath)
        print("\n\n**Script interrupted by user**\n\n")
    except Exception:
        traceback.print_exc(file=sys.stdout)
    sys.exit(0)

if __name__ == "__main__":
    main()
