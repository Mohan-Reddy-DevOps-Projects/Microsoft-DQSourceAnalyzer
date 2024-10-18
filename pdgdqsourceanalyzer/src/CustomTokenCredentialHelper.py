from azure.core.credentials import AccessToken

class CustomTokenCredential(object):
    def __init__(self,token,expires_on):
        self.token = token
        self.expires_on = expires_on

    def get_token(self, *scopes, **kwargs):
        return AccessToken(self.token, self.expires_on)