from .enums import Channel
from .channels import (
    DiscordChannel, 
    EmailChannel,
    PushChannel,
    SlackChannel,
    SMSChannel,
    TelegramChannel, 
    WhatsAppChannel
)


NOTIFICATION_CHANNELS = {
    Channel.DISCORD: DiscordChannel,
    Channel.EMAIL: EmailChannel,
    Channel.PUSH: PushChannel,
    Channel.SLACK: SlackChannel,
    Channel.SMS: SMSChannel,
    Channel.TELEGRAM: TelegramChannel,
    Channel.WHATSAPP: WhatsAppChannel
}
