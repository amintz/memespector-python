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
        for i in range(settings.procLimit):
            inputhandle.next()
            curimg = inputhandle.getCurImg()
            output.resetrow()
            printfuncs.itemProcess(i, settings.procLimit,curimg['path'],curimg['id'])
            output.loadimginfo()
            output.saveimg()

            if settings.downloadMode:
                output.writerow()
                continue
            else:
                # If there is a json annotation file saved in cache, use that
                if output.annotationexists():
                    printfuncs.annotationexisted()
                    goodparse = apirequest.loadResponse(output.annotationpath())
                else:
                    goodparse = apirequest.annotateImage(curimg)
                    output.saveannotation(apirequest.getResponseData())
                if goodparse:
                    output.loadparsedann(apirequest.getParsedResponse())
                    output.loadlabels(apirequest.getlabels())
                else:
                    printfuncs.exception(const.api_error_warning + output.annotationpath())
                    output.writerow()
                    continue

                # Write this image data to output file
                output.writerow()

        # Write data to graph file
        output.writelabelgraph()
    except KeyboardInterrupt:
        if not settings.downloadMode:
            output.writelabelgraph()
        printfuncs.interrupted()
