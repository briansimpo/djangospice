from django.db.models import TextChoices

class JobStatus(TextChoices):
    STARTED = "started", "Started"
    QUEUED = "queued", "Queued"
    RUNNING = "running", "Running"
    SUCCESS = "success", "Success"
    FAILURE = "failure", "Failure"
    RETRYING = "retrying", "Retrying"
    CANCELLED = "cancelled", "Cancelled"