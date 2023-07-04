from flask import Flask, request
from flask_socketio import SocketIO, join_room, leave_room
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")
login_manager = LoginManager(app)

class Phone(UserMixin): # a class to represent a phone
    def __init__(self, name):
        self.name = name
        self.id = uuid.uuid4().hex # generate a unique id for the phone

phones = {} # a dictionary to store information about each phone

def name_exists(name): # a function to check if a name is already in the dictionary
    return name in [phones[token].name for token in phones]

@login_manager.user_loader
def load_user(user_id): # a function to load a user by id
    return phones.get(user_id)

@socketio.on('connect')
def handle_connect():
    app.logger.info('logged in successfully')
    print('Client connected')
    print('Connection from ' + request.remote_addr)
    socketio.emit('message', {'data': 'hello from server'})
    
@socketio.on('message')
def handle_message(data):
    print('Message: ' + data)

@socketio.on('login')
def handle_login(data):
    token = data['token'] # get the token of the phone
    if token in phones: # check if the token is valid
        phone = phones[token] # get the phone object
        login_user(phone) # log in the phone using flask-login
        join_room(phone.id) # join a room with the phone id
        socketio.emit('message', {'data': f'Welcome back, {phone.name}'}, room=phone.id) # send a welcome message to the phone
    else:
        socketio.emit('message', {'data': 'Invalid token'}, room=request.sid) # send an error message to the phone

@socketio.on('disconnecting')
def handle_disconnecting():
    reason = request.args.get('reason') # get the reason for disconnecting
    if current_user.is_authenticated: # check if the user is logged in
        leave_room(current_user.id) # leave the room with the user id
        logout_user() # log out the user using flask-login
        print(f'{current_user.name} disconnected: {reason}')

@app.route('/check-name', methods=['GET'])
def check_name_api():
    name = request.args.get('name') # get the name parameter from the query string
    socketio.emit('message', {'data': 'hello from server, you just checked ' + name})
    if name:
        result = name_exists(name) # call the check_name function
        if result:
            return {'message': 'Name available'}, 200 # return a success message and status code
        else:
            return {'message': 'Name already taken'}, 400 # return an error message and status code
    else:
        return {'message': 'Missing name parameter'}, 400 # return an error message and status code

if __name__ == '__main__':
    socketio.run(app, port=80)
