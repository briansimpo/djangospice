from jsonfield.fields import JSONField
from model_utils import Choices
from django.utils import timezone
from django.conf import settings
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey  # noqa
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse, NoReverseMatch

from djangospice.database.models import BaseModel

from .querysets import NotificationQuerySet

def id2slug(notification_id):
    return notification_id + 110909

class Notification(BaseModel):
    """
    Action model describing the actor acting out a verb (on an optional
    target).
    Nomenclature based on http://activitystrea.ms/specs/atom/1.0/

    Generalized Format::

        <actor> <verb> <time>
        <actor> <verb> <target> <time>
        <actor> <verb> <action_object> <target> <time>

    Examples::

        <justquick> <reached level 60> <1 minute ago>
        <brosner> <commented on> <pinax/pinax> <2 hours ago>
        <washingtontimes> <started follow> <justquick> <8 minutes ago>
        <mitsuhiko> <closed> <issue 70> on <mitsuhiko/flask> <about 2 hours ago>

    Unicode Representation::

        justquick reached level 60 1 minute ago
        mitsuhiko closed issue 70 on mitsuhiko/flask 3 hours ago

    HTML Representation::

        <a href="http://oebfare.com/">brosner</a> commented on <a href="http://github.com/pinax/pinax">pinax/pinax</a> 2 hours ago # noqa

    """
    LEVELS = Choices('success', 'info', 'warning', 'error')
    level = models.CharField(_('level'), choices=LEVELS, default=LEVELS.info, max_length=20)

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('recipient'),
        blank=False,
    )
    unread = models.BooleanField(_('unread'), default=True, blank=False, db_index=True)

    actor_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='notify_actor',
        verbose_name=_('actor content type')
    )
    actor_object_id = models.CharField(_('actor object id'), max_length=255)
    actor = GenericForeignKey('actor_content_type', 'actor_object_id')
    actor.short_description = _('actor')

    verb = models.CharField(_('verb'), max_length=255)
    description = models.TextField(_('description'), blank=True, null=True)

    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='notify_target',
        verbose_name=_('target content type'),
        blank=True,
        null=True
    )
    target_object_id = models.CharField(_('target object id'), max_length=255, blank=True, null=True)
    target = GenericForeignKey('target_content_type', 'target_object_id')
    target.short_description = _('target')

    action_object_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='notify_action_object',
        verbose_name=_('action object content type'),
        blank=True,
        null=True
    )
    action_object_object_id = models.CharField(_('action object object id'), max_length=255, blank=True, null=True)
    action_object = GenericForeignKey('action_object_content_type', 'action_object_object_id')
    action_object.short_description = _('action object')

    timestamp = models.DateTimeField(_('timestamp'), default=timezone.now, db_index=True)

    public = models.BooleanField(_('public'), default=True, db_index=True)
    deleted = models.BooleanField(_('deleted'), default=False, db_index=True)
    emailed = models.BooleanField(_('emailed'), default=False, db_index=True)

    data = JSONField(_('data'), blank=True, null=True)

    objects = NotificationQuerySet.as_manager()

    class Meta:
        ordering = ('-timestamp',)
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(
                fields=[
                    "recipient",
                    "unread",
                ]
            )
        ]
       

    def __str__(self):
        ctx = {
            'actor': self.actor,
            'verb': self.verb,
            'action_object': self.action_object,
            'target': self.target,
            'timesince': self.timesince()
        }
        if self.target:
            if self.action_object:
                return _('%(actor)s %(verb)s %(action_object)s on %(target)s %(timesince)s ago') % ctx
            return _('%(actor)s %(verb)s %(target)s %(timesince)s ago') % ctx
        if self.action_object:
            return _('%(actor)s %(verb)s %(action_object)s %(timesince)s ago') % ctx
        return _('%(actor)s %(verb)s %(timesince)s ago') % ctx

    def timesince(self, now=None):
        """
        Shortcut for the ``django.utils.timesince.timesince`` function of the
        current timestamp.
        """
        from django.utils.timesince import timesince as timesince_
        return timesince_(self.timestamp, now)

    @property
    def slug(self):
        return id2slug(self.id)
    
    def mark_as_deleted(self):
        if not self.deleted:
            self.deleted = True
            self.save()
            
    def mark_as_undeleted(self):
        if self.deleted:
            self.deleted = False
            self.save()

    def mark_as_read(self):
        if self.unread:
            self.unread = False
            self.save()

    def mark_as_unread(self):
        if not self.unread:
            self.unread = True
            self.save()

    def actor_object_url(self):
        try:
            url = reverse("admin:{0}_{1}_change".format(self.actor_content_type.app_label,
                                                        self.actor_content_type.model),
                          args=(self.actor_object_id,))
            return format_html("<a href='{url}'>{id}</a>", url=url, id=self.actor_object_id)
        except NoReverseMatch:
            return self.actor_object_id

    def action_object_url(self):
        try:
            url = reverse("admin:{0}_{1}_change".format(self.action_object_content_type.app_label,
                                                        self.action_content_type.model),
                          args=(self.action_object_id,))
            return format_html("<a href='{url}'>{id}</a>", url=url, id=self.action_object_object_id)
        except NoReverseMatch:
            return self.action_object_object_id

    def target_object_url(self):
        try:
            url = reverse("admin:{0}_{1}_change".format(self.target_content_type.app_label,
                                                        self.target_content_type.model),
                          args=(self.target_object_id,))
            return format_html("<a href='{url}'>{id}</a>", url=url, id=self.target_object_id)
        except NoReverseMatch:
            return self.target_object_id
    
    def naturalday(self):
        """
        Shortcut for the ``humanize``.
        Take a parameter humanize_type. This parameter control the which humanize method use.
        Return ``today``, ``yesterday`` ,``now``, ``2 seconds ago``etc. 
        """
        from django.contrib.humanize.templatetags.humanize import naturalday
        return naturalday(self.timestamp)

    def naturaltime(self):
        from django.contrib.humanize.templatetags.humanize import naturaltime
        return naturaltime(self.timestamp)     

