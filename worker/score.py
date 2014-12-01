import json
import os
import requests
import subprocess

from .celery import app, config
from . import job_util, utils


@app.task(name='covalic_score', bind=True)
@job_util.task(logPrint=True)
def covalic_score(*args, **kwargs):
    localDirs = {}

    # Unzip the input files since they are folders
    for label, path in kwargs['_localInput'].iteritems():
        output = os.path.join(kwargs['_tmpDir'], label)
        utils.extractZip(path, output, flatten=True)
        localDirs[label] = output

    # Call our scoring executable, passing test data and grouth truth
    command = (
        os.path.abspath(config.get('covalic', 'score_executable')),
        '--submission', localDirs['submission'],
        '--ground_truth', localDirs['ground_truth']
    )
    p = subprocess.Popen(args=command, cwd=kwargs['_tmpDir'],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()

    if p.returncode != 0:
        print 'STDOUT: ' + stdout
        print 'STDERR: ' + stderr

        raise Exception('Scoring subprocess returned error code {}'.format(
            p.returncode))

    scoreTarget = kwargs['scoreTarget']
    httpMethod = getattr(requests, scoreTarget['method'].lower())
    req = httpMethod(scoreTarget['url'], headers=scoreTarget.get('headers'),
                 data=json.loads(stdout))
    req.raise_for_status()
