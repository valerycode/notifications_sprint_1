import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from .validators import validate_uuid, validate_datetime


class UUIDTimeStampedMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class NotificationTransport(models.TextChoices):
    EMAIL = 'email'
    PUSH = 'push'
    SMS = 'sms'
    WEBSOCKET = 'websocket'


class NotificationType(models.TextChoices):
    INFO = 'info'
    PROMO = 'promo'
    BONUS = 'bonus'


class Template(UUIDTimeStampedMixin, models.Model):
    name = models.CharField(_('Name'), max_length=254, unique=True, help_text="Template name")
    description = models.TextField(_('Description'), blank=True, null=True, help_text="Template description")
    subject = models.CharField(
        _('Subject'),
        max_length=254,
    )
    body = models.TextField(
        _('Body'),
    )

    class Meta:
        db_table = 'templates'
        verbose_name = _('Templates')
        verbose_name_plural = _('Templates')

    def __str__(self):
        return self.name


class NotificationSendStatus(models.TextChoices):
    WAITING = 'waiting', _('Waiting')
    FAILED = 'failed', _('Failed')
    DONE = 'done', _('Done')


class Notification(UUIDTimeStampedMixin, models.Model):
    name = models.CharField(_('Name'), max_length=254)
    description = models.TextField(_('Description'), blank=True, null=True)
    users_ids = ArrayField(
        models.CharField(max_length=255), validators=[validate_uuid], blank=True, null=True, default=list,
        help_text=_('Recipients UUIDs. For example: 74f4c5ff-2432-4594-ae49-2f9f48f274ed,'
                    ' 2b2a5654-7dd3-4ea4-ae19-0d9a4a7999ba'), verbose_name=_('Recipients'))
    template = models.ForeignKey(Template, on_delete=models.PROTECT, verbose_name=_('Template'))
    transport = models.CharField(
        _('Method of sending'), max_length=50,
        choices=NotificationTransport.choices
    )
    scheduled_time = models.DateTimeField(_("Time of sending"), validators=[validate_datetime])
    type = models.CharField(
        _('Type'),
        max_length=50,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
    )
    status = models.CharField(
        _('Status'),
        max_length=50,
        choices=NotificationSendStatus.choices,
        default=NotificationSendStatus.WAITING,
    )

    class Meta:
        db_table = 'notifications'
        verbose_name = _('Notifications')
        verbose_name_plural = _('Notifications')

    def __str__(self):
        return self.name
