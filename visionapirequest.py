import sys, requests, base64

class VisionApiRequest:
    def __init__(self, apiKey, setMaxResults=False, maxResults=10, labelDetection=False, safeSearchDetection=False, textDetection=False, webDetection=False, faceDetection=False):
        self.apiKey = apiKey
        self.setMaxResults = setMaxResults
        self.maxResults = maxResults
        self.modules={}
        self.modules['LABEL_DETECTION'] = labelDetection
        self.modules['SAFE_SEARCH_DETECTION'] = safeSearchDetection
        self.modules['TEXT_DETECTION'] = textDetection
        self.modules['WEB_DETECTION'] = webDetection
        self.modules['FACE_DETECTION'] = faceDetection
        self.response=""
        self.makeFeaturesJson()

    def printModuleConfiguration(self):
        print("\nGOOGLE VISION API SETTINGS\n\n\tActive modules ")
        for key in self.modules:
            if self.modules[key]:
                print("\t\t" + key)
        print("")
        if self.setMaxResults:
            print("\tMax number of results per analysed aspect\n\t\t" + self.maxResults, end="\n\n")
        else:
            print("\tMax number of results per aspect not set (using API default)")

    def makeFeaturesJson(self):
        features = []
        for key in self.modules:
            if self.modules[key]:
                if self.setMaxResults:
                    features.append('''{
                                    "type":"''' + key + '''",
                                    "maxResults":''' + self.maxResults + '''
                                 }''')
                else:
                    features.append('''{
                                    "type":"''' + key + '''"
                                 }''')
            else:
                continue
        self.featuresJson = ",\n\t\t\t".join(features)

    def annotateImage(self, path, isRemote, base64Encode=True):
        if not isRemote or base64Encode:
            if not isRemote:
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
                        ''' + self.featuresJson + '''
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
                        ''' + self.featuresJson + '''
                    ]
                    }
                  ]
                }
                '''
        print("done.")
        print("\tRequesting from Google Vision API...", end="")
        sys.stdout.flush()
        url = 'https://vision.googleapis.com/v1/images:annotate?key=' + self.apiKey;
        jsonResponse = requests.post(url, data=jsonRequest)
        print("done.")
        self.response = jsonResponse.json()

    def getResponse(self):
        return self.response
