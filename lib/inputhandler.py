import os, csv, sys, hashlib
from . import constants as const
from . import settings

class InputHandler:
    def __init__(self, settings):
        self.settings = settings
        self.path = self.settings.input
        self.imgcol = settings.imagesColumn
        self.linkcol = settings.linkColumn

        # Check if path exists
        if not os.path.exists(self.path):
            raise FileNotFoundError('Input file or path does not exist. Given:' + self.path)

        # Determine input type
        if os.path.isdir(self.path):
            self.inputtype = const.FOLDER
            settings.inputImageFolder=self.path
        elif os.path.isfile(self.path):
            self.pathext = os.path.splitext(self.path)[1]
            self.pathbase = os.path.basename
            if self.pathext == ".csv" or self.pathext == ".tab":
                self.inputtype = const.CSV
                if settings.delimiter == "":
                    if self.pathext == ".tab":
                        settings.delimiter="\t"
                    else:
                        settings.delimiter=","
                if self.imgcol == "":
                    raise NameError('Input file is of tabular type and image column has not been defined. Check configuration file or command arguments.')
            else:
                self.inputtype = const.TXT
        else:
            raise FileNotFoundError('Input file or path could not have type determined. Given:',self.path)

        settings.inputType = self.inputtype

        # If type is CSV or TXT, open file and prepare
        if not self.inputtype == const.FOLDER:
            # Load file
            self.file = open(self.path, encoding='utf8')

            # If file is CSV, prepare CSV DictReader
            if self.inputtype == const.CSV:
                try:
                    self.csvDialect = csv.Sniffer().sniff(self.file.read(1024), delimiters=settings.delimiter)
                    self.file.seek(0)
                except Exception as exc:
                    print(const.csv_dialect_error)
                    print(exc)

                if not self.csvDialect.escapechar:
                    self.csvDialect.escapechar = "\\"

                self.csv = csv.DictReader(self.file, delimiter=settings.delimiter)

                if self.imgcol not in self.csv.fieldnames:
                    raise KeyError('Could not find image column in input file.')
                if self.linkcol!="" and self.linkcol not in self.csv.fieldnames:
                    raise KeyError('Could not find link column in input file')
                elif self.linkcol == "":
                    self.linkcol = self.imgcol

                self.filelist = []
                for row in self.csv:
                    self.filelist.append(row[self.imgcol])
                self.file.seek(0)
                next(self.csv)
            # If file is TXT, prepare file list
            elif self.inputtype == const.TXT:
                self.filelist = self.file.readlines()
            else:
                raise RuntimeError('Input Handler Input Type is badly attributed')
        else:
            # If input is folder, preare list of contents
            fulllist = os.listdir(self.path)
            self.filelist = []
            # Filter files for image files
            supported_types=['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.ico', '.pdf', '.tiff']
            for file in fulllist:
                ext = os.path.splitext(file)[1]
                if ext in supported_types:
                    self.filelist.append(file)
            if len(self.filelist)==0:
                raise FileNotFoundError('Folder indicated as input does not contain image files.')

        settings.numImages = len(self.filelist)
        if settings.numImages < settings.procLimit:
            settings.procLimit = settings.numImages
        elif settings.procLimit == 0:
            settings.procLimit = settings.numImages
        self.iterindex = 0

    def update(self):
        try:
            imgpath = self.filelist[self.iterindex]

            if imgpath.startswith("http://") or imgpath.startswith("https://"):
                isremote = True
            else:
                isremote = False
                if not os.path.isabs(imgpath):
                    imgpath = os.path.join(settings.inputImageFolder, imgpath)

            imgfn = os.path.basename(imgpath)
            imgex = os.path.splitext(imgpath)[1]

            if "?" in imgex:
                imgex = imgex.split("?")[0]

            if not isremote:
                imgid = imgfn.split(".")[0]
            else:
                hashobj = hashlib.sha1(imgpath.encode('utf8'))
                imgid = hashobj.hexdigest()

            if self.inputtype == const.CSV:
                self.curRow = next(self.csv)
                link = self.curRow[self.linkcol]
            else:
                link = imgpath

            if isremote and settings.saveImageCopy:
                copyfn = imgid + imgex
                copyfp = os.path.join(settings.imageCpFolder, copyfn)
            else:
                copyfn = "NONE"
                copyfp = "NONE"

            self.curimg = {'id': imgid, 'path':imgpath, 'origfn': imgfn, 'ext': imgex, 'isremote': isremote, 'copyfn': copyfn, 'copyfp': copyfp, 'link': link}

            return True
        except IndexError:
            print("\n**END OF FILE**\n")
            return False
        except Exception as exc:
            print(exc)
            sys.exit()

    # Move to next entry in input file or to next image in folder

    def next(self):
        self.update()
        self.iterindex += 1

    def getCurImg(self):
        return self.curimg

    def getCurRow(self):
        if self.inputtype == const.CSV:
            return self.curRow
        else:
            return False

    def reset(self):
        self.iterindex=0
        self.file.seek(0)
        next(self.csv)
        curImg = self.filelist[self.iterindex]
        if self.inputtype == const.CSV:
            self.curRow = next(self.csv)

    def getNumImages(self):
        return len(self.filelist)

    def getInputType(self):
        return self.inputtype

    def getCSVDialect(self):
        return self.csv.dialect

    def getCSVFieldnames(self):
        return self.csv.fieldnames
