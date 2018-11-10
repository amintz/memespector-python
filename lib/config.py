import configparser, argparse, os, sys
from . import constants as const
from . import settings

def cleanQuotes(path):
    if (path.startswith('\'') and path.endswith('\'')) or (path.startswith('\"') and path.endswith('\"')):
       return path[1:-1]
    else:
        return path

def parsearg():
    parser = argparse.ArgumentParser(description='Process images through Google Cloud Vision API')
    parser.add_argument(    '--configfile',
                        metavar="CONFIG_PATH",
                        nargs=1,
                        default='NONE',
                        help='Receives string for path to config file. Use this in case you wish to override the default config file.'
                        )
    parser.add_argument(    '--downloadmode',
                        action='store_const',
                        const="DOWNLOAD_MODE",
                        default="NONE",
                        help="Use this to run script in download mode. No request to Google Cloud Vision API will be made, only images will be downloaded."
                        )
    # TODO: More command line options
    # parser.add_argument(    '--input',
    #                         metavar="INPUT_PATH",
    #                         nargs=1,
    #                         default='NONE',
    #                         required=False,
    #                         help='Receives string for path to file with image list or folder containing images to be processed. Required in case no config file is available.'
    #                     )
    # parser.add_argument(    '--imagecol',
    #                         nargs=1,
    #                         default='NONE',
    #                         help='Header of column in which to find image URLs or paths, if applicable'
    #                     )
    # parser.add_argument(    '--linkcol',
    #                         nargs=1,
    #                         default='NONE',
    #                         help='Receives string containing header of column in which to find URLs related to the image, if applicable'
    #                     )
    # parser.add_argument(    '--limit',
    #                         nargs=1,
    #                         type=int,
    #                         default=100,
    #                         help='Receives integer for maximum number of images to process. Defaults to 100, set to 0 to process all images.'
    #                     )
    # parser.add_argument(    '--key',
    #                         nargs=1,
    #                         default="NONE",
    #                         help='Receives string containing the API key for accessing Google\'s services.'
    #                     )
    # parser.add_argument(    '--modules',
    #                         nargs="+",
    #                         default="NONE",
    #                         choices=['label', 'safesearch', 'text', 'web', 'face'],
    #                         help='Indicate the module(s) you wish to request from the API. Options: label, safesearch, text, web, face'
    #                     )
    # parser.add_argument(    '--maxresults',
    #                         nargs=1,
    #                         default="NONE",
    #                         help='Receives integer for maximum number of results from the API modules. Do not set or set to 0 to get the API\'s default'
    #                     )
    # parser.add_argument(    '--dontsaveimages',
    #                         action="store_const",
    #                         const="NOT_SAVE",
    #                         default="NONE",
    #                         help="Use this to avoid script from downloading copies of processed images."
    #                     )
    return parser.parse_args()

def parseconfigfile(path="config.txt"):

    configfile = configparser.ConfigParser()

    try:
        configfile.read(path)
    except Exception as exc:
        print(exc)
        print(const.config_load_error)
        sys.exit()

    try:
        settings.input             = cleanQuotes(configfile.get('Input configuration','Input'))
        settings.projectFolder     = configfile.get('Project', 'projectFolder')

        if settings.input.endswith('/') or settings.input.endswith('\\'):
            settings.dir_path      = os.path.dirname(settings.input[:-1])
        else:
            settings.dir_path      = os.path.dirname(settings.input)
        settings.outputsFolder     = os.path.join(settings.dir_path, settings.projectFolder)
        settings.imageCpFolder     = os.path.join(settings.outputsFolder, configfile.get('Advanced settings','ImageCopyFolder'))
        settings.cacheFolder   = os.path.join(settings.outputsFolder, configfile.get('Advanced settings','CacheFolder'))
        settings.logsFolder        = os.path.join(settings.outputsFolder, configfile.get('Advanced settings', 'LogFolder'))

        settings.saveImageCopy     = configfile.getboolean('Output configuration','SaveImageCopy')
        settings.timeseries        = configfile.getboolean('Output configuration','TimeSeries')
        settings.labelThreshold    = configfile.getfloat('Output configuration','LabelScoreFilter')

        settings.forceBase64       = configfile.getboolean('Advanced settings','ForceBase64')
        settings.inputImageFolder  = cleanQuotes(configfile.get('Input configuration','InputImageFolder'))

        settings.delimiter         = configfile.get('Input configuration','Delimiter').encode('utf-8').decode('unicode_escape')

        settings.imagesColumn      = configfile.get('Input configuration','ImagesColumn')
        settings.linkColumn        = configfile.get('Input configuration','LinkColumn')

        if settings.linkColumn=="":
            settings.linkColumn = settings.imagesColumn

        settings.procLimit         = configfile.getint('Input configuration','Limit')

        settings.labelDetection    = configfile.getboolean('Api setup','Label')
        settings.safeSearchDetection = configfile.getboolean('Api setup','SafeSearch')
        settings.textDetection     = configfile.getboolean('Api setup','Text')
        settings.webDetection      = configfile.getboolean('Api setup','Web')
        settings.faceDetection     = configfile.getboolean('Api setup','Face')

        if not (settings.labelDetection or settings.safeSearchDetection or settings.textDetection or settings.webDetection or settings.faceDetection):
            settings.downloadMode = True
        else:
            settings.downloadMode = False

        settings.maxResults        = configfile.getint('Api setup','MaxResults')
        settings.apiKey            = configfile.get('Api setup','ApiKey')

        if settings.maxResults == 0:
            settings.setMaxResults = False
        else:
            settings.setMaxResults = True

    except Exception as exc:
        print(exc)
        print(const.config_parse_error)
        sys.exit()

def initconfig():
    args = parsearg()
    if args.configfile != 'NONE':
        parseconfigfile(args.configfile)
    else:
        parseconfigfile()
    if args.downloadmode != 'NONE':
        settings.downloadMode = True
