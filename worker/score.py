import os

from .celery import app, config
from . import utils


@app.task(name='covalic_score', bind=True)
def covalic_score(task, *args, **kwargs):
    tempDir = os.path.join('tmp', task.request.id)

    if not os.path.isdir(tempDir):
        os.makedirs(tempDir)

    files = utils.fetchInputs(tempDir, kwargs.get('input', ()))

    if kwargs.get('cleanup', True):
        utils.cleanup(tempDir)
