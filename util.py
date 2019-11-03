import boto3


def send_mail(subject, text, recipients):
    if type(recipients) not in (tuple, list):
        recipients = [recipients]

    ses = boto3.client("ses")
    ses.send_email(
        Source='awslimitchecker <noreply@example.com>',
        Destination={
            'ToAddresses': recipients
        },
        Message={
            "Subject": {
                'Data': subject,
                'Charset': 'utf-8'
            },
            "Body": {
                "Text": {
                    'Data': text,
                    'Charset': 'utf-8'
                }
            }
        }
    )
