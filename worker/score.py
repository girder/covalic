from .celery import app, config

@app.task
def score(*args, **kwargs):
    print args
    print kwargs
