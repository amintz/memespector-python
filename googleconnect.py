import base64, requests, sys, configparser
import functions as f

settings = configparser.ConfigParser()
settings._interpolation = configparser.ExtendedInterpolation()

try:
    settings.read('config.ini')
except Exception:
    sys.exit('\n**ERROR**\nCould not open configuration file. It should be in the same folder as the script and named \'config.ini\'\n')

try:
    imagesRemote = f.yn(settings['SourceImagesLocation']['ImagesRemote'])
    forceBase64 = f.yn(settings['SourceImagesLocation']['ForceBase64'])
    modules = {
        'LABEL_DETECTION'         : f.yn(settings['ApiRequestFeatures']['Label']),
        'SAFE_SEARCH_DETECTION'   : f.yn(settings['ApiRequestFeatures']['SafeSearch']),
        'TEXT_DETECTION'          : f.yn(settings['ApiRequestFeatures']['Text']),
        'WEB_DETECTION'           : f.yn(settings['ApiRequestFeatures']['Web']),
        'FACE_DETECTION'          : f.yn(settings['ApiRequestFeatures']['Face'])
    }
    maxResults = settings['ApiRequestFeatures']['MaxResults']
    apiKey = settings['ApiRequestFeatures']['ApiKey']
except Exception:
    sys.exit("\n**ERROR**\nCould not parse at least one of the settings from the config file. Please verify its contents carefully.")

if maxResults == "0":
    setMax = False
else:
    setMax = True




def printModuleConfiguration():

    print("\nGOOGLE VISION API SETTINGS\n\n\tActive modules ")

    for key in modules:
        if modules[key]:
            print("\t\t" + key)

    print("")

    print("\tMax number of results per analysed aspect\n\t\t" + maxResults, end="\n\n")

def jsonRequestFeatures() :
    features = []
    for key in modules:
        if modules[key]:
            if setMax:
                features.append('''{
                                "type":"''' + key + '''",
                                "maxResults":''' + maxResults + '''
                             }''')
            else:
                features.append('''{
                                "type":"''' + key + '''"
                             }''')
        else:
            continue
    jsonRequestFeatures = ",\n\t\t\t".join(features)

    return jsonRequestFeatures


def processImage(path, remote=imagesRemote):
    if not remote or forceBase64:

        if not remote:
            print("\tEncoding image in base64...", end="")
            sys.stdout.flush()
            try:
                image = open(path,"rb")
            except Exception:
                sys.exit('\n\t**ERROR**\n\tCould not open local image. Check if file exists and configuration file.\n')
            base64Data = base64.b64encode(image.read())
            print("done.")
        else:
            print("\tRetrieving remote image...", end="")
            sys.stdout.flush()
            try:
                image = requests.get(path,allow_redirects=True)
            except Exception:
                sys.exit('\n\t**ERROR**\n\tCould not retrieve remote image. Check data, internet connection, configuration.\n')
            if image.text == "":
                print('\n\t **ALERT** Could not retrieve remote image. Skipping to next.\n')
                return False
            base64Data = base64.b64encode(image.content)
            print("done.")
        print("\tPreparing request...", end="")
        sys.stdout.flush()
        jsonRequest = '''{
            "requests":[
                {
                "image":{
                    "content": "''' + base64Data.decode("utf-8") + '''"
                },
                "features":[
                    ''' + jsonRequestFeatures() + '''
                ]
                }
            ]
        }
        '''
    else:
        print("\tPreparing request...", end="")
        sys.stdout.flush()
        jsonRequest = '''{
            "requests":[
                {
                "image":{
                    "source": {
                        "imageUri": "''' + path + '''"
                    }
                },
                "features":[
                    ''' + jsonRequestFeatures() + '''
                ]
                }
              ]
            }
            '''
    print("done.")
    print("\tRequesting from Google Vision API...", end="")
    sys.stdout.flush()
    url = 'https://vision.googleapis.com/v1/images:annotate?key=' + apiKey;
    jsonResponse = requests.post(url, data=jsonRequest)
    print("done.")

    return jsonResponse.json()
