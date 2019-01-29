import os, csv, sys, datetime, json
from shutil import copyfile
import networkx as nx
from . import constants as const
from . import settings, printfuncs
from . import networkfunctions as net

class OutputHandler:
    def __init__(self, inputHandler):

        self.inputhandle = inputHandler

        # Establish current date and time
        self.datetime = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M")

        #-------------------
        # Create directories
        # ------------------

        if os.path.exists(settings.outputsFolder):
            if not settings.timeseries:
                answer = input("\nATTENTION: Project folder \"" + settings.projectFolder + "\" already exists. There is risk of overwriting files. Continue? Y or N > ")
                if answer.lower() == 'n':
                    sys.exit('Rename project in config file.')
                elif answer.lower() == 'y':
                    print('Continuing overwriting existing files.')
                else:
                    sys.exit('Answer not understood. Exiting.')
        else:
            os.makedirs(settings.outputsFolder)
        if not settings.downloadMode and not os.path.exists(settings.cacheFolder):
            os.makedirs(settings.cacheFolder)
        if (settings.saveImageCopy or settings.downloadMode) and not os.path.exists(settings.imageCpFolder):
            os.makedirs(settings.imageCpFolder)
        # TODO: Logging
        # if not os.path.exists(settings.logsFolder):
            # os.makedirs(settings.logsFolder)

        # Establish files basenames depending on inputType
        if settings.inputType == const.FOLDER:
            if settings.input.endswith('/') or settings.input.endswith('\\'):
                self.basename = os.path.basename(settings.input[:-1])
            else:
                self.basename = os.path.basename(settings.input)
        else:
            self.basename = os.path.basename(settings.input).split(".")[0]

        # TODO: Logging
        # Create log file
        # self.logfp = os.path.join(settings.logsFolder, self.basename + "_" + self.datetime + ".log")

        # ----------------------
        # Create CSV output file
        # ----------------------

        # CSV file name
        if settings.timeseries:
            self.csvfn = "annotated_" + self.basename + "_" + self.datetime + ".csv"
        else:
            self.csvfn = "annotated_" + self.basename + '.csv'

        # CSV file path
        self.csvfp = os.path.join(settings.outputsFolder,self.csvfn)

        # CSV file creation
        try:
            self.csvf = open(self.csvfp, 'w', newline='', encoding='utf8')
        except Exception as exc:
            print(const.output_csv_create_error)
            print(exc)

        # CSV fieldnames
        self.csvfields = ['original_filename', 'image_id', 'file_ext']
        if settings.saveImageCopy:
            self.csvfields += ['copy_filename']
        if settings.safeSearchDetection:
            self.csvfields += ['gv_ss_adult','gv_ss_spoof','gv_ss_medical','gv_ss_violence']
        if settings.labelDetection:
            self.csvfields += ['gv_labels']
        if settings.textDetection:
            self.csvfields += ['gv_text', 'gv_text_lang']
        if settings.webDetection:
            self.csvfields += ['gv_web_entities', 'gv_web_full_matching_images', 'gv_web_partial_matching_images', 'gv_web_pages_with_full_matching_images', 'gv_web_pages_with_partial_matching_images', 'gv_web_visually_similar_images']
        if settings.faceDetection:
            self.csvfields += ['gv_num_faces', 'gv_face_joy', 'gv_face_sorrow', 'gv_face_anger', 'gv_face_surprise']

        # if input type is CSV, get input CSV fieldnames
        if self.inputhandle.getInputType() == const.CSV:
            self.csvfields = self.inputhandle.getCSVFieldnames() + self.csvfields
            self.csv = csv.DictWriter(self.csvf, fieldnames=self.csvfields, dialect=self.inputhandle.getCSVDialect())
        else:
            self.csv = csv.DictWriter(self.csvf, fieldnames=self.csvfields, escapechar="\\", quoting=csv.QUOTE_ALL)

        self.csv.writeheader()

        # ----------------------
        # Create graph file
        # ----------------------

        self.labelgraph = nx.Graph()
        if settings.timeseries:
            self.labelgexffn = "img-label_" + self.basename + "_" + self.datetime + ".gexf"
        else:
            self.labelgexffn = "img-label_" + self.basename + '.gexf'
        self.labelgexffp = os.path.join(settings.outputsFolder,self.labelgexffn)

    # ----------------------
    # Reset current output row
    # ----------------------
    def resetrow(self):
        self.outrow = {}
        self.foundlabels = []
        if settings.inputType == const.CSV:
            self.inrow = self.inputhandle.getCurRow()
        else:
            self.inrow = {}

    # ----------------------
    # Save image copy 
    # ----------------------

    def saveimg(self):
        curimg = self.inputhandle.getCurImg()
        if (curimg['isremote'] or curimg['isabs']) and settings.saveImageCopy:
            printfuncs.copying()
            copyfp = curimg['copyfp']
            if not os.path.isfile(copyfp):
                if curimg['isremote']:
                    net.saveimage(curimg['path'], copyfp)
                else:
                    copyfile(curimg['path'], copyfp)
            else:
                printfuncs.copyexisted()

    # ----------------------
    # Check if annotation exists for the image
    # ----------------------

    def annotationexists(self):
        curimg = self.inputhandle.getCurImg()
        if settings.timeseries:
            self.annfp = os.path.join(settings.cacheFolder, curimg['id'] + "_" + self.datetime + ".json")
        else:
            self.annfp = os.path.join(settings.cacheFolder, curimg['id'] + ".json")
        return os.path.isfile(self.annfp)

    # ----------------------
    # Get annotation file path
    # ----------------------

    def annotationpath(self):
        return self.annfp
    
    # ----------------------
    # Load parsed annotation
    # ----------------------

    def loadparsedann(self, annotations):
        for key, val in annotations.items():
            self.updaterowval(key, val)

    # ----------------------
    # Load labels and add to graph
    # ----------------------

    def loadlabels(self, labels):
        curimg = self.inputhandle.getCurImg()
        if len(labels) > 0:
            for label in labels:
                if not label['id'] in self.foundlabels:
                    self.foundlabels.append(label['id'])
                    self.addlabelnode(label['id'], label['description'], label['mid'])
                self.addlabeledge(curimg['id'], label['id'], label['score'], label['topicality'])

    # ----------------------
    # Save annotation
    # ----------------------

    def saveannotation(self, data):
        try:
            with open(self.annfp, 'w', encoding='utf8') as ann:
                json.dump(data, ann, indent=4, sort_keys=True)
        except Exception:
            raise

    # ----------------------
    # Load current image information
    # ----------------------

    def loadimginfo(self):
        curimg = self.inputhandle.getCurImg()
        self.updaterowval('original_filename', curimg['origfn'])
        self.updaterowval('image_id', curimg['id'])
        self.updaterowval('file_ext', curimg['ext'])
        self.updaterowval('copy_filename', curimg['copyfn'])
        if curimg['copyfn'] == "NONE":
            self.addimagenode(curimg['id'], curimg['origfn'], curimg['link'])
        else:
            self.addimagenode(curimg['id'], curimg['copyfn'], curimg['link'])

    # ----------------------
    # Update row values
    # ----------------------

    def updaterowval(self, key, value):
        if key in self.csv.fieldnames:
            self.outrow[key] = value

    # ----------------------
    # Write row to CSV
    # ----------------------
    def writerow(self):
        row = {}

        for key, value in self.inrow.items():
            if key in self.csv.fieldnames:
                row[key] = value
        
        row = {**row, **self.outrow}

        self.csv.writerow(row)

    # ----------------------
    # Add Label node to graph
    # ----------------------
    def addlabelnode(self, id, description, mid):
        self.labelgraph.add_node(id, type='gv_label', label=description, mid=mid, description=description)

    # ----------------------
    # Add Image to Label edge to graph
    # ----------------------
    def addlabeledge(self, imageid, labelid, score, topicality):
         self.labelgraph.add_edge(imageid, labelid, score=score, topicality=topicality)

    # ----------------------
    # Add image node to graph
    # ----------------------
    def addimagenode(self, id, file, link):
        self.labelgraph.add_node(id, type='image', label='', file=file, link=link)
        for field in self.inrow:
            if (field in self.csv.fieldnames) and (field not in self.labelgraph.node[id]):
                self.labelgraph.node[id][field] = self.inrow[field]

    # ----------------------
    # Write graph file
    # ----------------------
    def writelabelgraph(self):
        # TODO: Option to automatically apply network layout
        if not settings.downloadMode:
            print("\n\nWriting image-label graph.")
            nx.write_gexf(self.labelgraph, self.labelgexffp)
            

    # ----------------------
    # Get date time
    # ----------------------
    def getDateTime(self):
        return self.datetime
