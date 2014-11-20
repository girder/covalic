import os
import re
import requests
import shutil


def _readFilenameFromResponse(request):
    """
    This helper will derive a filename from the HTTP response, first attempting
    to use the content disposition header, otherwise falling back to the last
    token of the URL.
    """
    print request.headers['Content-Disposition']
    match = re.search('filename="(.*)"', request.headers['Content-Disposition'])
    print match

    if match is None:
        return [t for t in request.url.split('/') if t][-1]
    else:
        return match.group(1)


def fetchHttpInput(tempDir, spec):
    """
    Downloads an input file via HTTP using requests.
    """
    if 'url' not in spec:
        raise Exception('No URL specified for HTTP input.')

    request = requests.get(spec['url'], headers=spec.get('headers', {}))
    request.raise_for_status()

    filename = spec.get('filename', _readFilenameFromResponse(request))
    path = os.path.join(tempDir, filename)

    with open(path, 'wb') as out:
        for buf in request.iter_content(32768):
            out.write(buf)

    return path


def fetchInputs(tempDir, inputList):
    """
    Fetch all inputs, return a list of corresponding local files. Right now,
    the only supported type is 'http'.
    """
    localFiles = []

    for input in inputList:
        inputType = input.get('type', 'http').lower()

        if inputType == 'http':
            localFiles.append(fetchHttpInput(tempDir, input))
        else:
            raise Exception('Invalid input type: ' + inputType)

    return localFiles


def cleanup(tempDir):
    """
    Cleanup from a job is performed by this function. For now, this is simply
    deleting the temp directory.

    :param tempDir: The temporary directory to remove.
    """
    if os.path.isdir(tempDir):
        shutil.rmtree(tempDir)
