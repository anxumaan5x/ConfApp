from enum import unique
import os
import pathlib
import re
from flask.helpers import get_load_dotenv
import requests
from datetime import datetime, time
import timedelta
from flask import Flask, session, abort, redirect, request, render_template, url_for
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref
app = Flask("Google Login App")
app.secret_key = "ddsdadw"
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db=SQLAlchemy(app)

import os
from flask import send_from_directory

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(50), nullable=False)
    google_id=db.Column(db.String(30), unique=True, nullable=False)

    chats = db.relationship('Chat', backref='user')

class Chat(db.Model):
    __tablename__ = 'chat'
    id = db.Column(db.Integer, primary_key=True)
    message=db.Column(db.String(1000), nullable=False)
    from_id=db.Column(db.String(30), db.ForeignKey('user.google_id'), nullable=False)
    to_id=db.Column(db.String(30), nullable=False)
    time=db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


def get_chats(from_id='112342845020655906267', to_id='1424567895645321456545'):
    timenow = datetime.utcnow()
# # printing initial_date
# print (ini_time_for_now)
    
    my_list=[from_id, to_id]
    reversed_list=my_list
    reversed_list.reverse()
    # my_dict={{}}
    chats_dict={}
    get_chat=Chat.query.filter(Chat.from_id.in_(my_list),Chat.to_id.in_(reversed_list)).order_by(Chat.time.asc()).all()
    index=0
    for chat in get_chat:
        chats_dict[index]={}
        # print(f'{chat.message}, Sender = {chat.user.name}, time = {chat.time}')
        td = timedelta.Timedelta(timenow - chat.time)
        if td.total.hours<=1:
            chats_dict[index]["timestamp"]=str(td.total.minutes) + ' minutes '
        elif td.total.hours<=24:
            chats_dict[index]["timestamp"]=str(td.total.hours) + ' hour '
        else:
            chats_dict[index]["timestamp"]=str(td.total.days) + ' days '
        chats_dict[index]["sender"] = chat.from_id
        chats_dict[index]["message"] = chat.message   
        index=index+1  
    return chats_dict
    # print(chats_dict)
    


#get all chats for one user
def all_chats(to_id='112342845020655906267'):
    get_chat=Chat.query.filter_by(to_id=to_id).group_by(Chat.from_id).all()
    my_dict={}
    user_received_chats_from=[]
    # print(get_chat)
    for chat in get_chat:
        user_received_chats_from.append(chat.from_id)
    for sender in user_received_chats_from:
        # print(f'Chats between {to_id} and {sender}')
        my_dict[sender]=get_chats(sender, to_id)        
        print("")
    # print(my_dict)
    return my_dict
    print(user_received_chats_from)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "143969115563-9u8ebmsoo2oj1ugc39p14ffhrktes5jr.apps.googleusercontent.com"
client_secrets_file = "client_secret.json"

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)


# def login_is_required(function):
#     def wrapper(*args, **kwargs):
#         if "google_id" not in session:
#             return redirect('/login') # Authorization required
#         else:
#             return function()
#     return wrapper

requestor = ''

def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            global requestor
            requestor=request.path
            print('Requestor: ' + requestor, flush=True)
            return redirect('/login') # Authorization required
        else:
            return function(*args, **kwargs)
    wrapper.__name__ = function.__name__
    return wrapper



@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )
    
    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    print(session["name"], session["google_id"], flush=True)
    query_user=User.query.filter_by(google_id=session['google_id']).first()
    if query_user is None:
        new_user=User(name=session['name'], google_id=session['google_id'])
        db.session.add(new_user)
        db.session.commit()
    global requestor
    print('Requestor is ' + requestor, flush=True)
    if requestor:
        return redirect(requestor)
    print("Tring to access " + '/' + session['google_id'], flush=True)
    return redirect('/' + session['google_id'])




@app.route("/logout")
def logout():
    session.clear()
    return "Logged out"


@app.route("/")
def index():
    return redirect('/login')

@app.route('/<user_id>', methods=['GET', 'POST'])
@login_is_required
def user_dashboard(user_id):    
    if session["google_id"]==user_id:
        if request.method == 'POST':
            message = request.form['message']
            sendto=request.form['send']
            # print(sendto, flush=True)
            newchat=Chat(message=message, from_id=session["google_id"], to_id=sendto)
            db.session.add(newchat)
            db.session.commit()
            return redirect(url_for('user_dashboard', user_id=user_id))
        chats=all_chats()
        return render_template('dashboard.html', chats = chats, me=session["google_id"])

    else:
        query_user=User.query.filter_by(google_id=user_id).first()
        try:
            
            length=len(query_user.name.split(' ')[0])
            user=query_user.name.split(' ')[0][0] + '*' * (length-1)
        except:
            return "User does not exist"
        if request.method == 'POST':
            message = request.form['message']
            sendto=request.form['send']
            # print(sendto, flush=True)
            newchat=Chat(message=message, from_id=session["google_id"], to_id=sendto)
            db.session.add(newchat)
            db.session.commit()
            return redirect(url_for('user_dashboard', user_id=user_id))
        chatsBetweenUser=get_chats(user_id,session['google_id'])
        # print(chatsBetweenUser, flush=True)
        # return f"<h1>Hello {query_user.name[0]}</h1>"
        return render_template('otheruser.html', chats = chatsBetweenUser, me=session["google_id"], user=user)
        # return "Hello"
    # print(chats)
    


# @app.route('/')
# def home():
#     return redirect('/' + session['google_id'])


@app.route("/def/protected_area")
@login_is_required
def protected_area():
    return f"Hello {session['name']}! <br/> <a href='/logout'><button>Logout</button></a>"

@app.route("/req")
def req():
    global requestor
    return f'<h1>Requestor is {requestor}</h1>'
if __name__ == "__main__":
    app.run()