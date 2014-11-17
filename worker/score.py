from .celery import app, config


@app.task(name='covalic_score')
def covalic_score(*args, **kwargs):
    print kwargs
