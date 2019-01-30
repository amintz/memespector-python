import sys, traceback
from . import visionapirequest, config, printfuncs, settings, inputhandler, outputhandler
from . import constants as const

def main():
    try:

        # Parse config file and command-line args
        config.initconfig()

        # Start input handler
        inputhandle = inputhandler.InputHandler(settings)

        # Create output files
        output = outputhandler.OutputHandler(inputhandle)

        # Configure Processing attributes
        apirequest = visionapirequest.VisionApiRequest()
        apirequest.printModuleConfiguration()

        printfuncs.imgSourceInit()
        printfuncs.inputInit()
        printfuncs.outputInit()

        # ----------------
        # Process images
        # ----------------

        # Keep track of labels found
        foundlabels = []
        error_count = 0

        for i in range(settings.procLimit):
            inputhandle.next()
            curimg = inputhandle.getCurImg()
            output.resetrow()
            printfuncs.itemProcess(i, settings.procLimit,curimg['path'],curimg['id'], error_count)
            output.loadimginfo()
            output.saveimg()

            if settings.downloadMode:
                output.writerow()
                continue
            else:
                # If there is a json annotation file saved in cache, use that
                if output.annotationexists():
                    try:
                        goodparse = apirequest.loadResponse(output.annotationpath())
                    except Warning:
                        goodparse = False
                        retry = True
                        printfuncs.annotationexistederror()
                    else:
                        printfuncs.annotationexisted()
                if not output.annotationexists():
                    try:
                        goodparse = apirequest.annotateImage(curimg)
                    except Warning:
                        goodparse = False
                    output.saveannotation(apirequest.getResponseData())
                if goodparse:
                    output.loadparsedann(apirequest.getParsedResponse())
                    output.loadlabels(apirequest.getlabels())
                else:
                    printfuncs.apierrorwarning(output.annotationpath())
                    output.writerow()
                    error_count += 1
                    continue

                # Write this image data to output file
                output.writerow()

        # Write data to graph file
        output.writelabelgraph()
    except KeyboardInterrupt:
        if not settings.downloadMode:
            output.writelabelgraph()
        printfuncs.interrupted()
