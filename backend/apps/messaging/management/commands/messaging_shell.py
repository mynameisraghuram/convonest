from apps.contacts.models import Contact
from apps.messaging.models import MessageLog, MessageDirection, MessageStatus

c = Contact.objects.first()

MessageLog.objects.create(
    direction=MessageDirection.INBOUND,
    msg_type="TEXT",
    status=MessageStatus.RECEIVED,
    contact=c,
    contact_phone=c.phone,
    body_text="Testing from shell",
)
