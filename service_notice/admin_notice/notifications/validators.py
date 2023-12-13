import uuid

from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_uuid(user_ids):
    for id in user_ids:
        try:
            uuid.UUID(id)
        except ValueError:
            raise ValidationError(
                _('%(id)s is not UUID'),
                params={'id': id},
            )


def validate_datetime(time):
    if time.strftime('%Y-%m-%dT%H:%M') < timezone.now().strftime('%Y-%m-%dT%H:%M'):
        raise ValidationError(
            _('Date and time cannot be earlier than the current ones!'),
        )
