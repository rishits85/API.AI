from database_setup import Base, User

def generate_auth_token(self, expiration = 600):
        s = Serializer(app.config['SECRET_KEY'], expires_in = expiration)
        print(s)
        return s.dumps({ 'id': self.id })

generate_auth_token(600)
