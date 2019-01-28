import requests
from . import printfuncs

def saveimage(url, filep):
    try:
        image = requests.get(url, allow_redirects=True, timeout=5)
        with open(filep, 'wb') as file:
            file.write(image.content)
    except Exception as exc:
        printfuncs.exception(exc)
        return False
    printfuncs.done()

def getimage(url):
    printfuncs.retrievingimg()
    try:
        image = requests.get(url, allow_redirects=True, timeout=5)
    except Exception as exc:
        printfuncs.exception(exc)
        return False
    printfuncs.done()
    return image.content

def getresponse(url, data):
    try:
        response = requests.post(url, data=data)
    except Exception as exc:
        printfuncs.exception(exc)
    return response
