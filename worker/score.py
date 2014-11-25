import os

from .celery import app, config
from . import utils


@app.task(name='covalic_score', bind=True)
def covalic_score(task, *args, **kwargs):
    tempDir = os.path.join('tmp', task.request.id)

    if not os.path.isdir(tempDir):
        os.makedirs(tempDir)

    try:
        inputs = kwargs.get('input', {})
        localFiles = utils.fetchInputs(tempDir, inputs)
    except:
        # TODO update job status and log.
        raise
    finally:
        if kwargs.get('cleanup', True):
            utils.cleanup(tempDir)
