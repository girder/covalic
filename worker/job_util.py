import functools
import os
import requests
import sys
import time
import traceback

from . import utils


class JobStatus(object):
    INACTIVE = 0
    QUEUED = 1
    RUNNING = 2
    SUCCESS = 3
    ERROR = 4
    CANCELED = 5


class JobManager(object):
    """
    This class is a context manager that can be used to write log messages to
    Girder by capturing stdout/stderr printed within the context and sending
    them in a rate-limited manner to Girder. This is not threadsafe.

    It also exposes utilities for updating other job fields such as progress
    and status.
    """
    def __init__(self, logPrint, url, method, headers={}, interval=0.5):
        """
        :param on: Whether print messages should be logged to the job log.
        :type on: bool
        :param url: The job update URL.
        :param method: The HTTP method to use when updating the job.
        :param headers: Optional HTTP header dict
        :param interval: Minimum time interval at which to send log updates
        back to Girder over HTTP (seconds).
        :type interval: int or float
        """
        self.logPrint = logPrint
        self.method = method
        self.url = url
        self.headers = headers
        self.interval = interval

        self._last = time.time()
        self._buf = ''

        if logPrint:
            self._pipes = sys.stdout, sys.stderr
            sys.stdout, sys.stderr = self, self

    def __enter__(self):
        return self

    def __exit__(self, excType, excValue, traceback):
        """
        When the context is exited, if we have a non-empty buffer, we flush
        the remaining contents and restore sys.stdout and sys.stderr to their
        previous values.
        """
        self._flush()

        if self.logPrint:
            sys.stdout, sys.stderr = self._pipes

    def _flush(self):
        """
        If there are contents in the buffer, send them up to the server. If the
        buffer is empty, this is a no-op.
        """
        if len(self._buf):
            httpMethod = getattr(requests, self.method.lower())

            httpMethod(self.url, headers=self.headers, data={'log': self._buf})
            self._buf = ''

    def write(self, message):
        """
        Append a message to the log for this job. If logPrint is enabled, this
        will be called whenever stdout or stderr is printed to. Otherwise it
        can be called manually and will still perform rate-limited flushing to
        the server.
        """
        self._buf += message
        if time.time() - self._last > self.interval:
            self._flush()
            self._last = time.time()

    def updateStatus(self, status):
        """
        Update the status field of a job.

        :param status: The status to set on the job.
        :type status: JobStatus
        """
        httpMethod = getattr(requests, self.method.lower())
        httpMethod(self.url, headers=self.headers, data={'status': status})


class task(object):
    """
    This decorator will perform many common job tasks including stdout/stderr
    writing to the job's log, automatic job status updates, creation and cleanup
    of the temp directory, and downloading of input files.
    """
    def __init__(self, logPrint=True, tmpDir=True):
        """
        :param logPrint: Whether print statements that occur within the inner
            function should be written to the Girder job log.
        :type logPrint: bool
        :param tmpDir: Whether a temp directory should be made for this task.
        :type tmpDir: bool
        """
        self.logPrint = logPrint
        self.tmpDir = tmpDir

    def _makeTmpDir(self, uuid, kwargs):
        if self.tmpDir:
            kwargs['_tmpDir'] = os.path.join('tmp', uuid)
            try:
                os.makedirs(kwargs['_tmpDir'])
            except OSError:
                if not os.path.isdir(kwargs['_tmpDir']):
                    raise
        else:
            kwargs['_tmpDir'] = None

    def __call__(self, fn):
        @functools.wraps(fn)
        def wrapped(task, *args, **kwargs):
            update = kwargs['jobUpdate']
            with JobManager(self.logPrint, update['url'], update['method'],
                            update['headers']) as jobMgr:
                try:
                    self._makeTmpDir(task.request.id, kwargs)
                    kwargs['_localInput'] = utils.fetchInputs(
                        kwargs['_tmpDir'], kwargs.get('input', {}))
                    oldCwd = os.getcwd()
                    retVal = fn(task, jobMgr, *args, **kwargs)
                    jobMgr.updateStatus(JobStatus.SUCCESS)
                    return retVal
                except:
                    t, val, tb = sys.exc_info()
                    msg = '{}: {}\n{}'.format(t.__name__, val,
                                              traceback.extract_tb(tb))
                    jobMgr.write(msg)
                    jobMgr.updateStatus(JobStatus.ERROR)
                    raise  # Raise so that celery also sees the exception
                finally:
                    os.chdir(oldCwd)
                    if kwargs.get('cleanup', True) and self.tmpDir:
                        utils.cleanup(kwargs['_tmpDir'])
        return wrapped
