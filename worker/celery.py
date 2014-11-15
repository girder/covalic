from __future__ import absolute_import

import celery
import os

from ConfigParser import ConfigParser

_cfgFiles = ('worker.dist.cfg', 'worker.local.cfg')
config = ConfigParser()
config.read([os.path.join(os.path.dirname(os.path.dirname(__file__)), f)
             for f in _cfgFiles])

app = celery.Celery(
    main=config.get('celery', 'app_main'),
    broker=config.get('celery', 'broker'),
    include=('worker.score',))
