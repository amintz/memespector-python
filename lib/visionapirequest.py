import base64
import re
import json
import os
from . import settings, printfuncs
from . import networkfunctions as net
from . import constants as const

class VisionApiRequest:
    def __init__(self):
        self.apiKey = settings.apiKey
        self.setMaxResults = settings.setMaxResults
        self.maxResults = settings.maxResults
        self.modules={}
        self.modules['LABEL_DETECTION'] = settings.labelDetection
        self.modules['SAFE_SEARCH_DETECTION'] = settings.safeSearchDetection
        self.modules['TEXT_DETECTION'] = settings.textDetection
        self.modules['WEB_DETECTION'] = settings.webDetection
        self.modules['FACE_DETECTION'] = settings.faceDetection
        self.response=""
        self.parsedresponse={   'gv_ss_adult':      'NONE',
                                'gv_ss_spoof':      'NONE',
                                'gv_ss_medical':    'NONE',
                                'gv_ss_violence':   'NONE',
                                'gv_labels':        'NONE',
                                'gv_text':          'NONE',
                                'gv_text_lang':     'NONE',
                                'gv_web_entities':  'NONE',
                                'gv_web_full_matching_images':              'NONE',
                                'gv_web_partial_matching_images':           'NONE',
                                'gv_web_pages_with_full_matching_images':   'NONE',
                                'gv_web_pages_with_partial_matching_images':'NONE',
                                'gv_web_visually_similar_images':           'NONE',
                                'gv_num_faces':     'NONE',
                                'gv_face_joy':      'NONE',
                                'gv_face_sorrow':   'NONE',
                                'gv_face_anger':    'NONE',
                                'gv_face_surprise': 'NONE'
                            }
        self.labels = []
        self.web_entities = []
        self.web_full_matching_images = []
        self.web_partial_matching_images = []
        self.web_visually_similar_images = []
        self.web_pages_with_full_matching_images = []
        self.web_pages_with_partial_matching_images = []
        self.makeFeaturesJson()

    def cleanParsedResponse(self):
        for key, value in self.parsedresponse.items():
            self.parsedresponse[key] = "NONE"
        self.labels = []
        self.web_entities = []
        self.web_full_matching_images = []
        self.web_partial_matching_images = []
        self.web_visually_similar_images = []
        self.web_pages_with_full_matching_images = []
        self.web_pages_with_partial_matching_images = []

    def printModuleConfiguration(self):
        printfuncs.printlog("\nGOOGLE VISION API SETTINGS\n\n\tActive modules ")
        for key in self.modules:
            if self.modules[key]:
                printfuncs.printlog("\t\t" + key)
        printfuncs.printlog("")
        if self.setMaxResults:
            printfuncs.printlog("\tMax number of results per analysed aspect\n\t\t" + str(self.maxResults), end="\n\n")
        else:
            printfuncs.printlog("\tMax number of results per aspect not set (using API default)")

    def likelihoodCompare(self, one, two):
        if one == 'UNDETECTED':
            return two
        elif one == 'UNKNOWN' and not (two == 'UNDETECTED'):
            return two
        elif one == 'VERY_UNLIKELY' and not (two == 'UNDETECTED' or two == 'UNKNOWN'):
            return two
        elif one == 'UNLIKELY' and not (two == 'UNDETECTED' or two == 'UNKNOWN' or two == 'VERY_UNLIKELY'):
            return two
        elif one == 'POSSIBLE' and not (two == 'UNDETECTED' or two == 'UNKNOWN' or two == 'VERY_UNLIKELY' or two == 'UNLIKELY'):
            return two
        elif one == 'LIKELY' and not (two == 'UNDETECTED' or two == 'UNKNOWN' or two == 'VERY_UNLIKELY' or two == 'UNLIKELY'  or two == 'POSSIBLE'):
            return two
        else:
            return one

    def makeFeaturesJson(self):
        features = []
        for key in self.modules:
            if self.modules[key]:
                if self.setMaxResults:
                    features.append('''{
                                    "type":"''' + key + '''",
                                    "maxResults":''' + str(self.maxResults) + '''
                                 }''')
                else:
                    features.append('''{
                                    "type":"''' + key + '''"
                                 }''')
            else:
                continue
        self.featuresJson = ",\n\t\t\t".join(features)

    def parseReponse(self):
        self.cleanParsedResponse()

        if 'responses' in self.response:
            responseNode = self.response['responses'][0]        
        elif 'error' in self.response:
            message = self.response['error']['message']
            code = self.response['error']['code']
            if code==400:
                raise Warning("\n**ERROR**\nAPI returned a 'Bad Request' error. Might be a problem with you API key or with the image file or url - check it is accesssible and not corrupted.")
            elif code==403 or code==401:
                raise Exception("\n**ERROR**\nAPI returned a 'Permission denied' or a 'Unauthorized' error. Might be a problem with the API key")
            else:
                raise Warning("\n**ERROR**\nAPI returned an error. Check file in 'annotations' folder for more information.")
        else:
            raise ValueError("API returned an invalid response. Check annotation file.")
            
        # Safe Search
        if settings.safeSearchDetection:
            if 'safeSearchAnnotation' in responseNode:
                self.parsedresponse['gv_ss_adult'] = responseNode['safeSearchAnnotation']['adult']
                self.parsedresponse['gv_ss_spoof'] = responseNode['safeSearchAnnotation']['spoof']
                self.parsedresponse['gv_ss_medical'] = responseNode['safeSearchAnnotation']['medical']
                self.parsedresponse['gv_ss_violence'] = responseNode['safeSearchAnnotation']['violence']

        # Labels
        if settings.labelDetection:
            if 'labelAnnotations' in responseNode:
                gv_labels = []
                for label in responseNode['labelAnnotations']:
                    if 'score' in label:
                        labelDict = {}
                        if label['score'] < settings.labelThreshold:
                            continue;
                        if label['mid']=='':
                            labelid = "_" + label['description']
                        else:
                            labelid = label['mid']
                    else:
                        continue
                    labelDict['id'] = labelid
                    labelDict['mid'] = label['mid']
                    labelDict['description'] = label['description']
                    labelDict['score'] = label['score']
                    labelDict['topicality'] = label['topicality']
                    self.labels.append(labelDict)
                    gv_labels.append(labelDict['description'] + " (" + str(labelDict['score']) + ")")
                self.parsedresponse['gv_labels'] = ";".join(gv_labels)

        # Text
        if settings.textDetection:
            if 'textAnnotations' in responseNode:
                self.parsedresponse['gv_text'] = responseNode['textAnnotations'][0]['description']
                self.parsedresponse['gv_text'] = re.sub("[\n\t\r]", " ", self.parsedresponse['gv_text'])
                self.parsedresponse['gv_text_lang'] = responseNode['textAnnotations'][0]['locale']

        # Web Detection
        if settings.webDetection:
            if 'webDetection' in responseNode:
                if 'fullMatchingImages' in responseNode['webDetection']:
                    for url in responseNode['webDetection']['fullMatchingImages']:
                        self.web_full_matching_images.append(url['url'].replace(",", "%2C"))
                    self.parsedresponse['gv_web_full_matching_images'] = ";".join(self.web_full_matching_images)
                if 'pagesWithMatchingImages' in responseNode['webDetection']:
                    for page in responseNode['webDetection']['pagesWithMatchingImages']:
                        if 'fullMatchingImages' in page:
                            self.web_pages_with_full_matching_images.append(page['url'].replace(",", "%2C"))
                        elif 'partialMatchingImages' in page:
                            self.web_pages_with_partial_matching_images.append(page['url'].replace(",", "%2C"))
                    if len(self.web_pages_with_full_matching_images) > 0:
                        self.parsedresponse['gv_web_pages_with_full_matching_images'] = ";".join(self.web_pages_with_full_matching_images)
                    if len(self.web_pages_with_partial_matching_images) > 0:
                        self.parsedresponse['gv_web_pages_with_partial_matching_images'] = ";".join(self.web_pages_with_partial_matching_images)
                if 'partialMatchingImages' in responseNode['webDetection']:
                    for url in responseNode['webDetection']['partialMatchingImages']:
                        self.web_partial_matching_images.append(url['url'].replace(",", "%2C"))
                    self.parsedresponse['gv_web_partial_matching_images'] = ";".join(self.web_partial_matching_images)
                if 'visuallySimilarImages' in responseNode['webDetection']:
                    for url in responseNode['webDetection']['visuallySimilarImages']:
                        self.web_visually_similar_images.append(url['url'].replace(",", "%2C"))
                    self.parsedresponse['gv_web_visually_similar_images'] = ";".join(self.web_visually_similar_images)
                if 'webEntities' in responseNode['webDetection']:
                    gv_web_entities = []
                    for entity in responseNode['webDetection']['webEntities']:
                        entityDict = {}
                        if 'description' in entity:
                            entityDict['description'] = entity['description']
                        else:
                            entityDict['description'] = "NONE"
                        if 'score' in entity:
                            entityDict['score'] = entity['score']
                            # gv_web_entities.append(description + "(" + str(entity['score']) + ")")
                        else:
                            entityDict['score'] = "NONE"
                        self.web_entities.append(entityDict)
                        gv_web_entities.append(entityDict['description'] + " (" + str(entityDict['score']) + ")")
                    self.parsedresponse['gv_web_entities'] = ";".join(gv_web_entities)

        # Face
        if settings.faceDetection:
            if 'faceAnnotations' in responseNode:
                self.parsedresponse['gv_num_faces'] = 0;
                self.parsedresponse['gv_face_joy'] = 'VERY_UNLIKELY'
                self.parsedresponse['gv_face_sorrow'] = 'VERY_UNLIKELY'
                self.parsedresponse['gv_face_anger'] = 'VERY_UNLIKELY'
                self.parsedresponse['gv_face_surprise'] = 'VERY_UNLIKELY'
                for face in responseNode['faceAnnotations']:
                    self.parsedresponse['gv_face_joy'] = self.likelihoodCompare(self.parsedresponse['gv_face_joy'], face['joyLikelihood'])
                    self.parsedresponse['gv_face_sorrow'] = self.likelihoodCompare(self.parsedresponse['gv_face_sorrow'], face['sorrowLikelihood'])
                    self.parsedresponse['gv_face_anger'] = self.likelihoodCompare(self.parsedresponse['gv_face_anger'], face['angerLikelihood'])
                    self.parsedresponse['gv_face_surprise'] = self.likelihoodCompare(self.parsedresponse['gv_face_surprise'], face['surpriseLikelihood'])
                    self.parsedresponse['gv_num_faces'] +=1

        return True

    def annotateImage(self, img):
        self.response=""
        if not img['isremote']:
            if os.path.isfile(img['path']):
                path = img['path']
                isremote = False
            else:
                isremote=True
                printfuncs.exception("File not found")
                return False
        else:
            if os.path.isfile(img['copyfp']):
                path = img['copyfp']
                isremote = False
            else:
                path = img['path']
                isremote = True

        if settings.forceBase64 or not isremote:
            if not isremote:
                try:
                    image = open(path,"rb")
                except Exception:
                    printfuncs.exception("Could not open local image or image copy")
                base64Data = base64.b64encode(image.read())
            else:
                image = net.getimage(path)
                base64Data = base64.b64b64encode(image)
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
        url = const.api_url + self.apiKey
        printfuncs.requesting()
        jsonResponse = net.getresponse(url, jsonRequest)
        printfuncs.printlog("done.")
        self.response = jsonResponse.json()
        return self.parseReponse()

    def getParsedResponse(self):
        return self.parsedresponse

    def getlabels(self):
        return self.labels

    def getResponseData(self):
        return self.response

    def loadResponse(self, annotationfp):
        response = json.load(open(annotationfp, encoding='utf8'))
        self.response = response
        goodparse = self.parseReponse()
        return goodparse
