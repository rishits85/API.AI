from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
import random
import string

Base = declarative_base()
secret_key = "secret_key"
#''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    hotel = Column(String(250), nullable=False)
    room = Column(String(250), nullable=False)
    location = Column(String(250), nullable=False)
    password = Column(String(250))
    token = Column(String(250))

    #This returns the unique id associated with the token
    def generate_auth_token(self, expiration = 600):
        token = "token"
        #''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
        return token
    #This can be made to live for an hour. As of now it lives forever to reduce traffic from multiple requests for refreshing the token
    def generate_access_token(self):
        s = Serializer(secret_key)
        return s.dumps({ 'id': self.id })

    @staticmethod
    def verify_auth_token(token):
            s = Serializer(secret_key)
            try:
                data = s.loads(token)
            except SignatureExpired:
                return None # valid token, but expired
            except BadSignature:
                return None # invalid token
            user = User.query.get(data['id'])
            return user

# class Restaurant(Base):
#     __tablename__ = 'restaurant'

#     id = Column(Integer, primary_key=True)
#     name = Column(String(250), nullable=False)
#     user_id = Column(Integer, ForeignKey('user.id'))
#     user = relationship(User)

#     @property
#     def serialize(self):
#         """Return object data in easily serializeable format"""
#         return {
#             'name': self.name,
#             'id': self.id,
#         }


# class MenuItem(Base):
#     __tablename__ = 'menu_item'

#     name = Column(String(80), nullable=False)
#     id = Column(Integer, primary_key=True)
#     description = Column(String(250))
#     price = Column(String(8))
#     course = Column(String(250))
#     restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
#     restaurant = relationship(Restaurant)
#     user_id = Column(Integer, ForeignKey('user.id'))
#     user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'price': self.price,
            'course': self.course,
        }


engine = create_engine('sqlite:///restaurantmenuwithusers.db')


Base.metadata.create_all(engine)
