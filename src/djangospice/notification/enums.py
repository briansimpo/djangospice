from django.db import models


class NotificationLevel(models.TextChoices):
    INFO = "INFO", "Info"
    SUCCESS = "SUCCESS", "Success"
    WARNING = "WARNING", "Warning"
    ERROR = "ERROR", "Error"


class NotificationVerb(models.TextChoices):
    NOTIFICATION = "NOTIFICATION", "Notification"
    MESSAGE = "MESSAGE", "Message"
    ANNOUNCEMENT = "ANNOUNCEMENT", "Announcement"
    ALERT = "ALERT", "Alert"
    REMINDER = "REMINDER", "Reminder"


class Channel(models.TextChoices):
    EMAIL = "email", "Email"
    PUSH = "push", "Push"
    SMS = "sms", "SMS"
    DISCORD = "discord", "Discord"
    SLACK = "slack", "Slack"
    TELEGRAM = "telegram", "Telegram"
    WHATSAPP = "whatsapp", "Whatsapp"


class DeliveryStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    SENT = "SENT", "Sent"
    DELIVERED = "DELIVERED", "Delivered"
    READ = "READ", "Read"
    FAILED = "FAILED", "Failed"
    RETRYING = "RETRYING", "Retrying"
    CANCELLED = "CANCELLED", "Cancelled"
    
    
class Platform(models.TextChoices):
    ANDROID = "ANDROID", "Android"
    IOS = "IOS", "iOS"
    WINDOWS = "WINDOWS", "Windows"
    MACOS = "MACOS", "macOS"
    LINUX = "LINUX", "Linux"
    WEB = "WEB", "Web"