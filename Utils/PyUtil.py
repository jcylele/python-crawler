import base64


def decodeBase64(b64string):
    padding = 4 - (len(b64string) % 4) if len(b64string) % 4 else 0
    padded_b64string = b64string + '=' * padding
    return base64.urlsafe_b64decode(padded_b64string).decode('utf-8')

def encodeBase64(string):
    return base64.urlsafe_b64encode(string.encode('utf-8')).decode('utf-8')
