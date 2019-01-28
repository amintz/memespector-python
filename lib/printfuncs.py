import sys
from . import constants as const
from . import settings

# TODO: Reorganize printing functions and message constants

def printlog(text="", end="\n"):
    # log.write(text+end)
    print(text, end=end)
    if end=="":
        sys.stdout.flush()

def startup():
    printlog(const.startup)

def imgSourceInit():
    printlog("\nHANDLING OF IMAGE SOURCE\n")
    if settings.forceBase64:
        printlog("\tLocal intermediation of data submission (forcing base64)")
    else:
        printlog("\tRemotely retrieved by Google")
    if settings.saveImageCopy:
        printlog("\tSaving local copies of processed images (if not local)")
    else:
        printlog("\tNot saving local copies")
    printlog("\tReading relative file paths (if provided) as relative to: " + settings.inputImageFolder)
    printlog()

def inputInit():
    printlog("DATA FILE\n")
    printlog("\tInput path\n\t\t" + settings.input)
    printlog("\tNumber of entries\n\t\t" + str(settings.numImages))
    printlog("\tProcessing limit\n\t\t" + str(settings.procLimit))
    printlog("\tImage column header\n\t\t" + settings.imagesColumn)

def outputInit():
    printlog("OUTPUT SETTINGS\n")
    printlog("\tOutputs folder\n\t\t" + settings.outputsFolder)
    printlog("\tImage copy folder\n\t\t" + settings.imageCpFolder)
    printlog("\tCache folder\n\t\t" + settings.cacheFolder)
    printlog("\n-------------------------")

def itemProcess(i, limit, path, id):
    printlog("\nImage " + str(i+1) + " of " + str(limit))
    printlog("\tImage path: " + path)
    printlog("\tImage ID: " + id)

def copying():
    printlog("\tCopying image...", end="")

def retrievingimg():
    printlog("\tRetrieving remote image...", end="")

def requesting():
    printlog("\tRequesting from Google Vision API...", end="")

def done():
    printlog("done.")

def copyexisted():
    printlog("copy already existed")

def annotationexisted():
    printlog("\t*ATTENTION* Using cached content located in the 'annotations' folder. Delete files if you wish to reprocess images.")

def apierrorwarning():
    printlog('\t*ATTENTION* Vision API returned an error for this image. Check JSON file for details.\n\tMoving on to next image.\n')

def interrupted():
    printlog("\n\n**Script interrupted by user**\n\n")

def exception(exc):
    printlog(const.warning_head + "\t" + str(exc))
