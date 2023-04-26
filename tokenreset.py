from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
def token(name,seconds):
    s=Serializer('8#5&890@0',seconds)
    return s.dumps({'user':name}).decode('utf-8')
