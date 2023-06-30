import requests
from app.models import CompanySettings

def send_msg(user, reciever, text, msg_type):
    settings = CompanySettings.objects.filter(company=user.company).first()
    
    is_true = False
    # url = 'http://91.204.239.42:8083/broker-api/send'
    if msg_type == 'mark':
        if settings.mark:
            is_true = True
    if msg_type == 'payment':
        if settings.payment:
            is_true = True
    if msg_type == 'attendace':
        if settings.attendace:
            is_true = True

    if is_true:

        url = settings.api_link

        headers = {'Content-type': 'application/json',  # Определение типа данных
                'Accept': 'text/plain',
                'Authorization': f'Basic {settings.key}'}
        data = {
            "messages":
            [
                {
                    "recipient": reciever,
                    "message-id": "3700",

                    "sms": {

                        "originator": settings.originator,
                        "content": {
                            "text": text
                        }
                    }
                }
            ]
        }
        response = requests.post(url, json=data, headers=headers)
        return response.status_code
