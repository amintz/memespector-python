import os

projectFolder     = "memespector-outputs"

dir_path          = os.getcwd()
outputsFolder     = os.path.join(dir_path, projectFolder)
logsFolder        = os.path.join(outputsFolder, "log")
imageCpFolder     = os.path.join(outputsFolder, "img")
cacheFolder   = os.path.join(outputsFolder, "annotations")

forceBase64       = True
saveImageCopy     = True
inputImageFolder  = ""

timeseries        = False
labelThreshold    = 0

input             = "default.csv"
delimiter         = ","
imagesColumn      = "imgurl"
linkColumn        = "default"

procLimit         = 20

labelDetection    = False
safeSearchDetection = False
textDetection     = False
webDetection      = False
faceDetection     = False

downloadMode       = True

maxResults        = 0
setMaxResults     = False

apiKey            = "NONONONONONONONONO"
