from celery import shared_task
from djangospice.core.serializer import deserialize
from .worker import JobWorker


@shared_task(bind=True)
def execute_job(self, serialized_job):
    """
    Background worker entry point.
    Reconstructs the original Python class instance containing its database models.
    """
    job = deserialize(serialized_job)
    
    # Hand execution control over to the worker unit
    return JobWorker(task=self).execute(job)