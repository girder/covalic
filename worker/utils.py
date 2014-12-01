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
    match = re.search('filename="(.*)"', request.headers['Content-Disposition'])

    if match is None:
        return [t for t in request.url.split('/') if t][-1]
    else:
        return match.group(1)


def fetchHttpInput(tmpDir, spec):
    """
    Downloads an input file via HTTP using requests.
    """
    if 'url' not in spec:
        raise Exception('No URL specified for HTTP input.')

    request = requests.get(spec['url'], headers=spec.get('headers', {}))
    request.raise_for_status()

    filename = spec.get('filename', _readFilenameFromResponse(request))
    path = os.path.join(tmpDir, filename)

    total = 0
    maxSize = spec.get('maxSize')

    with open(path, 'wb') as out:
        for buf in request.iter_content(32768):
            length = len(buf)
            if maxSize and length + total > maxSize:
                raise Exception('Exceeded max download size of {} bytes.'
                                .format(maxSize))
            out.write(buf)
            total += length

    return path


def fetchInputs(tmpDir, inputList):
    """
    Fetch all inputs. For each input, writes a '_localPath' key into the
    input spec that denotes where the file was written on the local disk.
    """
    localFiles = {}

    for label, input in inputList.iteritems():
        inputType = input.get('type', 'http').lower()

        if inputType == 'http':
            localFiles[label] = fetchHttpInput(tmpDir, input)
        else:
            raise Exception('Invalid input type: ' + inputType)

    return localFiles

def cleanup(tmpDir):
    """
    Cleanup from a job is performed by this function. For now, this is simply
    deleting the temp directory.

    :param tmpDir: The temporary directory to remove.
    """
    if os.path.isdir(tmpDir):
        shutil.rmtree(tmpDir)
