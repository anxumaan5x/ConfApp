from enum import unique
from json.decoder import JSONDecodeError
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
app.config['SQLALCHEMY_DATABASE_URI']=os.environ.get('DATABASE_URL')
# app.config['SQLALCHEMY_DATABASE_URI']=DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db=SQLAlchemy(app)
import os.path


import os
from flask import send_from_directory
import string
ALPHABET = string.ascii_uppercase + string.ascii_lowercase + \
           string.digits + '-_'
ALPHABET_REVERSE = dict((c, i) for (i, c) in enumerate(ALPHABET))
BASE = len(ALPHABET)
SIGN_CHARACTER = '$'

def num_encode(n):
    if n < 0:
        return SIGN_CHARACTER + num_encode(-n)
    s = []
    while True:
        n, r = divmod(n, BASE)
        s.append(ALPHABET[r])
        if n == 0: break
    return ''.join(reversed(s))

def num_decode(s):
    if s[0] == SIGN_CHARACTER:
        return -num_decode(s[1:])
    n = 0
    for c in s:
        n = n * BASE + ALPHABET_REVERSE[c]
    return n



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

class Report(db.Model):
    __tablename__ = 'reported'
    id = db.Column(db.Integer, primary_key=True)
    reported_by=db.Column(db.String(30), nullable=False)
    reported=db.Column(db.String(30), nullable=False)
    time=db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


def get_chats(from_id, to_id):
    timenow = datetime.utcnow()
# # printing initial_date
# print (ini_time_for_now)
    
    my_list=[from_id, to_id]
    reversed_list=my_list
    reversed_list.reverse()
    # my_dict={{}}
    chats_dict={}
    # get_chat=Chat.query.filter(Chat.from_id.in_(my_list),Chat.to_id.in_(reversed_list)).order_by(Chat.time.asc()).all()
    get_chat=Chat.query.filter(Chat.from_id.in_(my_list),Chat.to_id.in_(reversed_list)).order_by(Chat.time.asc())
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
def all_chats(to_id):
    get_chat=Chat.query.filter_by(to_id=Chat.to_id).group_by(Chat.from_id)
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
    redirect_uri="https://anotext.herokuapp.com/callback"
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
    my_id=num_encode(int(session['google_id']))
    print(my_id, flush=True)
    return redirect('/' + my_id)




@app.route("/logout")
def logout():
    session.clear()
    return redirect('/')


@app.route("/")
def index():
    if "google_id" not in session:
        return render_template('login.html')
    else:
        return redirect(url_for('user_dashboard', userstr=num_encode(int(session['google_id']))))

@app.route('/<userstr>', methods=['GET', 'POST'])
@login_is_required
def user_dashboard(userstr):
    user_id=str(num_decode(userstr))
    count=Report.query.filter_by(reported=session['google_id']).count()
    if count>5:
        return "You have been very naughty. And you got reported a lot"
    guser=User.query.filter_by(google_id=session["google_id"]).first()
    gname=guser.name.split(' ')[0]
    if session["google_id"]==user_id:
        if request.method == 'POST':
            message = request.form['message']
            sendto=request.form['send']
            # print(sendto, flush=True)
            newchat=Chat(message=message, from_id=session["google_id"], to_id=sendto)
            db.session.add(newchat)
            db.session.commit()
            print('Redirect to user id ' + userstr, flush=True)
            return redirect(url_for('user_dashboard', userstr=userstr))
        chats=all_chats(to_id=session["google_id"])
        return render_template('dashboard.html', chats = chats, me=session["google_id"], name=gname, usertag=userstr)

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
            sendtoid=str(num_decode(sendto))
            print(type(sendtoid) ,sendtoid, flush=True)
            # print(sendto, flush=True)
            newchat=Chat(message=message, from_id=session["google_id"], to_id=sendtoid)
            db.session.add(newchat)
            db.session.commit()
            return redirect(url_for('user_dashboard', userstr=userstr))
        chatsBetweenUser=get_chats(user_id,session['google_id'])
        # print(chatsBetweenUser, flush=True)
        # return f"<h1>Hello {query_user.name[0]}</h1>"
        return render_template('otheruser.html', chats = chatsBetweenUser, me=session["google_id"], user=user, name=gname, usertag=userstr)
        # return "Hello"
    # print(chats)

@app.route('/report/<num>')
@login_is_required
def report(num):
    try:
        user_id=str(int(num))
    except:
        user_id=str(num_decode(num))
    
    timenow = datetime.utcnow()
    latestreported=Report.query.filter_by(reported_by=session['google_id'], reported=user_id).order_by(Report.id.desc()).first()
    try:
        timedifference = timedelta.Timedelta(timenow - latestreported.time)
        if timedifference.total.hours<1:
            return "You must wait 1 hour before you can report the user again."
    except:
        pass
    
    reports=Report(reported_by=session['google_id'], reported=user_id)
    db.session.add(reports)
    db.session.commit()
    my_list=[session['google_id'], user_id]
    reversed_list=my_list
    reversed_list.reverse()
    db.session.query(Chat).filter(Chat.from_id.in_(my_list),Chat.to_id.in_(reversed_list)).delete()
    db.session.commit()
    return "Reported"

    


# @app.route('/')
# def home():
#     return redirect('/' + session['google_id'])


@app.route("/def/protected_area")
@login_is_required
def protected_area():
    return f"Hello {session['name']}! <br/> <a href='/logout'><button>Logout</button></a>"

@app.route('/copy/copy')
def copy():
    return render_template('login.html')

@app.route("/req")
def req():
    global requestor
    return f'<h1>Requestor is {requestor}</h1>'
if __name__ == "__main__":
    app.run()



# latestreported=Report.query.filter_by(reported_by='112342845020655906267', reported='117634559943903595921').order_by(Report.id.desc()).first()

# db.session.query(Report).delete()

# db.session.commit()