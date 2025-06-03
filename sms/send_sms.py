from kavenegar import *
from urllib.error import HTTPError


def send_sms_with_template(receptor, tokens: dict, template):
    """
        sending sms that needs template
    """
    try:
        api = KavenegarAPI(
            '74706450737042437176616D6C6C6937615375316132675A3731464B4F76382B6C4C51555241776678306B3D'
        )
        params = {
            'receptor': receptor,
            'template': template,
            'sender': '10008663',
        }
        for key, value in tokens.items():
            params[key] = value

        response = api.verify_lookup(params)
        print(response)
        return True
    except APIException as e:
        print(e)
        return False
    except HTTPError as e:
        print(e)
        return False


def send_sms_normal(receptor, message):
    try:
        api = KavenegarAPI(
            '74706450737042437176616D6C6C6937615375316132675A3731464B4F76382B6C4C51555241776678306B3D')
        params_buyer = {
            'receptor': receptor,
            'message': message,
            'sender': '10008663',
        }
        response = api.sms_send(params_buyer)
        print(response)
    except APIException as e:
        print(e)
    except HTTPError as e:
        print(e)
