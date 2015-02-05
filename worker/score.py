import json
import os
import requests
import subprocess

from .celery import app, config
from . import job_util, utils


def matchInputFile(gt, inputDir):
    """
    Given a ground truth file and an input directory, find a matching input
    file in the input directory (i.e. one with the same prefix but different
    extension). If none exists, raises an exception.
    """
    prefix = gt.split('.')[0]

    for input in os.listdir(inputDir):
        if input.split('.')[0] == prefix:
            return prefix, os.path.join(inputDir, input)

    raise Exception('No matching input file for prefix: ' + prefix)


def runScoring(truth, test, tmpDir):
    """
    Call our scoring executable on a single truth/input pair. Returns the
    resulting parsed metric values as a list of dicts containing "name" and
    "value" pairs.
    """
    if config.getboolean('covalic', 'docker_container_scoring'):
        volumeMap = '%s:%s' % (os.path.abspath(tmpDir), '/data')
        command = (
            'docker', 'run', '-v', volumeMap, 'girder/covalic-metrics',
            '/data/ground_truth/' + os.path.basename(truth),
            '/data/submission/' + os.path.basename(test)
        )
    else:
        command = (
            os.path.abspath(config.get('covalic', 'alt_score_exe')),
            truth, test
        )

    p = subprocess.Popen(args=command, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()

    if p.returncode != 0:
        print('Error scoring %s:' % truth)
        print('Command: ' + ' '.join(command))
        print('STDOUT: ' + stdout)
        print('STDERR: ' + stderr)

        raise Exception('Scoring subprocess returned error code {}'.format(
            p.returncode))

    metrics = []
    for line in stdout.splitlines():
        name, value = line.split('=')
        metrics.append({
            'name': name,
            'value': value
        })

    return metrics


@app.task(name='covalic_score', bind=True)
@job_util.task(logPrint=True, progress=True)
def covalic_score(*args, **kwargs):
    localDirs = {}
    jobMgr = kwargs['_jobManager']

    # Unzip the input files since they are folders
    for label, path in kwargs['_localInput'].iteritems():
        output = os.path.join(kwargs['_tmpDir'], label)
        utils.extractZip(path, output, flatten=True)
        localDirs[label] = output

    # Count the total number of files for progress reporting
    total = len(os.listdir(localDirs['ground_truth']))
    current = 0

    jobMgr.updateProgress(total=total, current=current)

    # Iterate over each file and call scoring executable on the pair
    scores = []
    for gt in os.listdir(localDirs['ground_truth']):
        current += 1

        prefix, input = matchInputFile(gt, localDirs['submission'])
        truth = os.path.join(localDirs['ground_truth'], gt)

        jobMgr.updateProgress(
            current=current, message='Scoring dataset %d of %d'
            % (current, total), forceFlush=(current == 1))

        scores.append({
            'dataset': gt,
            'metrics': runScoring(truth, input, kwargs['_tmpDir'])
        })

    jobMgr.updateProgress(message='Sending scores to server')

    scoreTarget = kwargs['scoreTarget']
    httpMethod = getattr(requests, scoreTarget['method'].lower())
    req = httpMethod(scoreTarget['url'], headers=scoreTarget.get('headers'),
                     data=json.dumps(scores))
    try:
        req.raise_for_status()
    except:
        print 'Posting score failed (%s). Response: %s' % \
            (scoreTarget['url'], req.text)
        raise

    jobMgr.updateProgress(message='Done')
