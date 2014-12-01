import os

from .celery import app, config
from . import job_util


@app.task(name='covalic_score', bind=True)
@job_util.task(logPrint=True)
def covalic_score(*args, **kwargs):
    print args
    print kwargs
