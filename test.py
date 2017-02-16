import urllib
import json
import os
import string
import random

from flask import Flask,render_template,request
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User
from flask import Flask,render_template
from flask import request
from flask import make_response
from flask import session as login_session
from flask import make_response
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash


# Flask app should start in global layout
app = Flask(__name__)
auth = HTTPBasicAuth()


@app.route('/', methods=['POST','GET'])
def webhook():
    req = request.get_json(silent=True, force=True)
    print("Request:")
    print(json.dumps(req, indent=4))

    #Check Amenities
    if req.get("result").get("action") == "Amenities-list":
        print("hello world");
        speech = "hello world"
        action = req.get("result").get("action")
        contextOut = [{
            "name": "temperature",
            "parameters": {
            "temperature": action,
            "temperature.original": "temperature"
            },
              "lifespan": 5
             }]
        data = []
        displayText = speech
        source = "myWebHook"
        return makeWebhookResponse2(speech,displayText, contextOut, data, source)

    #Update tempertature
    elif req.get("result").get("action") == "update_temperature":
        print "update temp called"
        return updateTemperature(req)
            
    else:
        contextOut = []
        print("screw world")
        speech = "fuck you world"
        data = []
        displayText = speech
        source = "myWebHook"
        return makeWebhookResponse2(speech,displayText, contextOut, data, source)


def updateTemperature(req):
    data = []
    source = "myWebHook"
    #First time agent is called
    if req.get("result").get("metadata").get("intentName") == "Update Temperature":
        print("agent called for first time")
        temperature = req.get("result").get("parameters").get("temperature")
        print temperature 
        contextOut = [{
            "name": "temperature",
            "parameters": {
            "temperature": temperature,
            "temperature.original": temperature
            },
              "lifespan": 5
             }]

        speech = "OK, Your temperature will be updated to " + temperature + " degress. Is that correct?"
        displayText= speech
        
        return makeWebhookResponse2(speech,displayText, contextOut, data, source)
        
        #User confirms correct temperature
    elif req.get("result").get("metadata").get("intentName") == "1.1-Correct Temperature":
        contextOut = []
        temperature = req.get("result").get("parameters").get("temperature") 
        #url = ('http://roomControllerURI:8080/integrated_services/:versionId/device/set_thermostat_setpoint?id=:%s&value=:%s'%(id,new_temperature))
        url = ('https://www.google.com/')
        response = urllib.urlopen(url)
        b= response.getcode()
        if b == 200:
            set_temperature = temperature #result['response']['newValue']
            speech = "Your room temperature is now set to " + set_temperature + " degrees Farenheit"
        else:
            speech = "Sorry, I was unable to process your request. Please contact front desk for further assistance " 
        
        displayText= speech
       
        #User says temperature is wrong
    elif req.get("result").get("metadata").get("intentName") == "1.2 Wrong":
        temperature = req['result']['contexts'][1]['parameters']['temperature']
        contextOut = [{
            "name": "new_temperature",
            "parameters": {
            "temperature": temperature,
            "temperature.original": temperature
            },
            "lifespan": 5
            }
        ]
        speech = "OK, Let's try again. What temperature would you like to set?"
        displayText= speech
        
            
    else:
        temperature = req.get("result").get("parameters").get("temperature")
        contextOut = []
        speech = "OK, Your temperature will now be updated to " + temperature + " degrees. Is that correct?"
        displayText= speech
    #Return the response 
    return makeWebhookResponse2(speech,displayText, contextOut, data, source)

def makeWebhookResponse2(speech,displayText, contextOut, data, source):
    response = {        
        "speech": speech,
        "displayText": speech,
        "data":data,
        "contextOut": contextOut,
        "source": source
        }
    final_response = make_response(json.dumps(response, indent=4))
    final_response.headers['Content-Type'] = 'application/json'
        
    return final_response  

@app.route('/authenticateUser')
def authenticateUser():
    response_type = request.args.getlist('response_type')
    client_id = request.args.getlist('client_id')
    redirect_uri = request.args.getlist('redirect_uri')
    state = request.args.getlist('state')
    #Check Client id is valid. This is configured by us on google portal
    if client_id[0] != "client_id":
        return ("invalid client id.")
    #Check redirect URI is valid. This is configured by us on google portal
    if redirect_uri[0] != "https://oauth-redirect.googleusercontent.com/r/apiai-157320":
        return ("invalid redirect URI. This URI does not belong to this application")
    #Check Client id is valid. This should be of type "code"
    if response_type[0] != "code":
        return("invalid response type")
    print state[0]
    #Store the above parameters in a login session
    login_session['client_id'] = client_id[0]
    login_session['state'] = state[0] 
    return render_template('SignUp.html', STATE="state")

@app.route('/token', methods = ['POST'])
#@auth.login_required
def exchageToken():
    client_id = request.args.getlist('client_id')
    client_secret = request.args.getlist('client_secret')
    code = request.args.getlist('code')
    grant_type = request.args.getlist('grant_type')
    if grant_type == authorization_code:
        user_id = User.verify_auth_token(code)
        if user_id:
            user = session.query(User).filter_by(id = user_id).one()
            token = user.generate_access_token()
            #update the db with this token
            # Return Below JSON Objcet
            # {
            #   token_type: "bearer",
            #   access_token: "ACCESS_TOKEN",
            #   refresh_token: "REFRESH_TOKEN"
            # }
        else:
            return False

        return True

@app.route('/signup', methods=['GET', 'POST'])
def signUp():
    print ("SignUp called")
    #Load the data from the ajax request you received and store it in a login. It will be stored in request.json 
    data = request.json
    login_session['hotel'] = data['hotel']
    login_session['room'] = data['room']
    login_session['location'] = data['location']
    print(login_session['hotel'])
    print(login_session['room'])
    print(login_session['location'])
    #check if the hotel and room are already in the database
    user = session.query(User).filter_by(hotel=login_session['hotel']).one()
    #if not call create user 
    if user is None:
        new_user = createUser(login_session)
        #generate authorization token and send to the client as a json object
        auth_code= new_user.generate_auth_token(600)
        params = {'auth':auth_code, 'state' : login_session['state']}
        response = make_response(json.dumps(params))
        #add the created user to global variable for use by other methods.
        g.user = new_user
    #if yes return accound already exists
    else:
        response = make_response(json.dumps('This user already exists try loggin in.'), 401)
        response.headers['Content-Type'] = 'application/json'

    return response

def createUser(login_session):
    print("createUser called")
    newUser = User(room=login_session['room'], hotel=login_session[
                   'hotel'], location= login_session['hotel'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    print ("user created successfully")
    return user

def updateUser(login_session):
    print("updateUser called")
    # newUser = User(room=login_session['room'], hotel=login_session[
    #                'hotel'], location= login_session['hotel'])
    # session.add(newUser)
    # session.commit()
    # user = session.query(User).filter_by(email=login_session['email']).one()
    print ("user updated successfully")
    return user.id


@auth.verify_password
def verify_pw(username_or_token, password):
    #Try to see if it's a token first
    user_id = User.verify_auth_token(username_or_token)
    if user_id:
        user = session.query(User).filter_by(id = user_id).one()
    else:
        user = session.query(User).filter_by(username = username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True

#Same name hotels differentiation
    # 1) Login with MHI
    # 2) Use location
    # 3) Have them enter the address/ ZipCode / 

  
if __name__ == '__main__':

    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    port = int(os.getenv('PORT', 8080))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')


# def processRequest(req):

#     baseurl = "https://query.yahooapis.com/v1/public/yql?"
#     yql_query = makeYqlQuery(req)
#     yql_url = baseurl + urllib.urlencode({'q': yql_query}) + "&format=json"
#     result = urllib.urlopen(yql_url).read()
#     data = json.loads(result)
#     res = makeWebhookResult(data)
#     return res


# def makeYqlQuery(req):
#     result = req.get("result")
#     parameters = result.get("parameters")
#     city = parameters.get("geo-city")
#     if city is None:
#         return None

#     return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "')"
