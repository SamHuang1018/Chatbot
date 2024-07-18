# USER_HTML_TEMPLATE = '''
# <!DOCTYPE html>
# <html>
# <head>
#     <title>客服聊天室 - 用戶</title>
#     <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
#     <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
#     <script type="text/javascript" charset="utf-8">
#         var socket = io();
#         var role = "使用者";

#         document.addEventListener('DOMContentLoaded', function() {
#             var input = document.getElementById('input');
#             var form = document.getElementById('form');
#             var chat = document.getElementById('chat');

#             form.onsubmit = function(e) {
#                 e.preventDefault();
#                 if (input.value) {
#                     socket.emit('chat message', {message: input.value, role: role});
#                     input.value = '';
#                 }
#             };

#             socket.on('chat message', function(msg) {
#                 var item = document.createElement('li');
#                 item.className = 'list-group-item';
#                 item.textContent = msg.role + ': ' + msg.message;
#                 chat.appendChild(item);
#                 window.scrollTo(0, document.body.scrollHeight);
#             });
#         });
#     </script>
# </head>
# <body>
#     <div class="container">
#         <ul id="chat" class="list-group mt-3"></ul>
#         <form id="form" class="form-inline mt-3 mb-3">
#             <input id="input" class="form-control mr-sm-2" type="text" autocomplete="off" placeholder="輸入您的問題">
#             <button class="btn btn-success my-2 my-sm-0" type="submit">發送</button>
#         </form>
#     </div>
# </body>
# </html>
# '''

# ADMIN_HTML_TEMPLATE = '''
# <!DOCTYPE html>
# <html>
# <head>
#     <title>客服聊天室 - 商家</title>
#     <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
#     <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
#     <script type="text/javascript" charset="utf-8">
#         var socket = io();
#         var role = "商家";

#         document.addEventListener('DOMContentLoaded', function() {
#             var input = document.getElementById('input');
#             var form = document.getElementById('form');
#             var chat = document.getElementById('chat');
#             var user_list = document.getElementById('user_list');

#             form.onsubmit = function(e) {
#                 e.preventDefault();
#                 if (input.value) {
#                     socket.emit('chat message', {message: input.value, role: role});
#                     input.value = '';
#                 }
#             };

#             socket.on('chat message', function(msg) {
#                 var item = document.createElement('li');
#                 item.className = 'list-group-item';
#                 item.textContent = msg.role + ': ' + msg.message;
#                 chat.appendChild(item);
#                 window.scrollTo(0, document.body.scrollHeight);
#             });

#             socket.on('update_users', function(users) {
#                 user_list.innerHTML = '';
#                 users.forEach(function(user) {
#                     var option = document.createElement('option');
#                     option.text = user;
#                     option.value = user;
#                     user_list.appendChild(option);
#                 });
#             });
#         });

#         function switchRoom() {
#             var user_id = user_list.value;
#             socket.emit('switch room', {new_room: user_id});
#         }
#     </script>
# </head>
# <body>
#     <div class="container">
#         <select id="user_list" onchange="switchRoom()" class="form-control mb-3">
#             <!-- 用戶列表在這裡動態生成 -->
#         </select>
#         <ul id="chat" class="list-group mt-3"></ul>
#         <form id="form" class="form-inline mt-3 mb-3">
#             <input id="input" class="form-control mr-sm-2" type="text" autocomplete="off" placeholder="回答問題">
#             <button class="btn btn-success my-2 my-sm-0" type="submit">發送</button>
#         </form>
#     </div>
# </body>
# </html>
# '''

# from flask import Flask, render_template_string, request, session
# from flask_socketio import SocketIO, emit, join_room, leave_room

# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'your_secret_key_here'
# socketio = SocketIO(app)

# users_rooms = {}

# @app.route('/')
# def user():
#     return render_template_string(USER_HTML_TEMPLATE)

# @app.route('/admin')
# def admin():
#     return render_template_string(ADMIN_HTML_TEMPLATE)

# @socketio.on('connect')
# def handle_connect():
#     user_id = request.sid
#     room_id = user_id
#     users_rooms[user_id] = room_id
#     join_room(room_id)
#     session['current_room'] = room_id
#     emit('update_users', list(users_rooms.keys()), broadcast=True)

# @socketio.on('disconnect')
# def handle_disconnect():
#     user_id = request.sid
#     room_id = users_rooms.get(user_id)
#     if room_id:
#         leave_room(room_id)
#         del users_rooms[user_id]
#         emit('update_users', list(users_rooms.keys()), broadcast=True)

# @socketio.on('switch room')
# def handle_switch_room(data):
#     new_room = data['new_room']
#     leave_room(session['current_room'])
#     join_room(new_room)
#     session['current_room'] = new_room
#     emit('chat message', {'role': 'System', 'message': f"你正在與{new_room}聊天"}, room=new_room)

# @socketio.on('chat message')
# def handle_message(data):
#     message = data['message']
#     role = data['role']
#     emit('chat message', {'message': message, 'role': role}, room=session['current_room'])

# if __name__ == '__main__':
#     socketio.run(app, debug=True, host='0.0.0.0')


# USER_HTML_TEMPLATE = '''
# <!DOCTYPE html>
# <html>
# <head>
#     <title>客服聊天室 - 用戶</title>
#     <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
#     <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
#     <style>
#         body {
#             background-color: #ececec;
#             font-family: Arial, sans-serif;
#             color: #333;
#         }
#         #chat {
#             margin-bottom: 10px;
#             overflow-y: auto;
#             height: 400px;
#             border: 1px solid #ccc;
#             padding: 10px;
#             background-color: #f9f9f9;
#         }
#         .list-group-item {
#             background-color: #e6ffed; /* Light green background */
#             border: 1px solid #97f295; /* Slightly darker green border */
#             border-radius: 15px;
#             margin-bottom: 5px;
#             padding: 10px 20px;
#         }
#         .list-group-item {
#             background-color: #f8f9fa;
#             border: none;
#             border-radius: 10px; /* 方圓形狀 */
#             margin-bottom: 10px;
#             padding: 10px 15px;
#             position: relative;
#             max-width: 80%;
#         }
#         .list-group-item.user-message {
#             background-color: #30cfd0; /* Line user message color */
#             color: #ffffff;
#             margin-left: auto; /* Align to the right */
#         }
#         #nameForm, #chatForm {
#             margin-top: 20px;
#         }
#         #input, #nameInput {
#             width: 70%;
#             margin-right: 10px;
#         }
#     </style>
#     <script type="text/javascript" charset="utf-8">
#         var socket = io();
#         var role = "使用者";
#         var userName = '';

#         document.addEventListener('DOMContentLoaded', function() {
#             var nameInput = document.getElementById('nameInput');
#             var chatForm = document.getElementById('chatForm');
#             var chat = document.getElementById('chat');
#             var nameForm = document.getElementById('nameForm');
#             var input = document.getElementById('input');

#             nameForm.onsubmit = function(e) {
#                 e.preventDefault();
#                 if (nameInput.value) {
#                     userName = nameInput.value;
#                     socket.emit('register user', userName);
#                     nameForm.style.display = 'none';
#                     chatForm.style.display = 'block';
#                 }
#             };

#             chatForm.onsubmit = function(e) {
#                 e.preventDefault();
#                 if (input.value) {
#                     socket.emit('chat message', {message: input.value, role: role, name: userName});
#                     input.value = '';
#                 }
#             };

#             socket.on('chat message', function(msg) {
#                 var item = document.createElement('li');
#                 item.className = 'list-group-item';
#                 item.textContent = msg.role + ': ' + msg.message;
#                 chat.appendChild(item);
#                 window.scrollTo(0, document.body.scrollHeight);
#             });

#         });
#     </script>
# </head>
# <body>
#     <div class="container">
#         <form id="nameForm" class="form-inline mt-3 mb-3">
#             <input id="nameInput" class="form-control mr-sm-2" type="text" placeholder="輸入您在line的名稱" autocomplete="off">
#             <button class="btn btn-primary my-2 my-sm-0" type="submit">發送</button>
#         </form>
#         <ul id="chat" class="list-group mt-3"></ul>
#         <form id="chatForm" class="form-inline mt-3 mb-3" style="display:none;">
#             <input id="input" class="form-control mr-sm-2" type="text" autocomplete="off" placeholder="輸入您的問題">
#             <button class="btn btn-success my-2 my-sm-0" type="submit">發送</button>
#         </form>
#     </div>
# </body>
# </html>
# '''

USER_HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>客服聊天室 - 用戶</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <style>
        body {
            background-color: #f0f2f5;
            font-family: Arial, sans-serif;
        }
        #chat {
            margin-bottom: 10px;
            overflow-y: auto;
            height: 400px;
            border: 1px solid #ccc;
            padding: 10px;
            background-color: #ffffff;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .list-group-item {
            background-color: #f8f9fa;
            border: none;
            border-radius: 18px;
            margin-bottom: 10px;
            padding: 10px 20px;
            position: relative;
            display: flex;
            align-items: center;
            max-width: 80%;
            word-wrap: break-word;
            justify-content: space-between;
            align-items: center;
        }
        .list-group-item.user-message {
            background-color: #d9fdd3;
            color: #000;
            margin-left: auto;
            align-self: flex-end;
            text-align: right;
        }
        .list-group-item.admin-message {
            align-self: flex-start;
            text-align: left;
        }
        .list-group-item.timestamp {
            display: inline-block;
            font-size: 0.8em;
            color: #666;
            margin-left: 10px; /* For space between message and timestamp */
            white-space: nowrap;
            flex-shrink: 0;
        }
        #input, #nameInput {
            width: 70%; /* Updated width */
            margin-right: 10px; /* Added margin */
        }
        #sendButton {
            width: 80px; /* Ensure consistent button width */
        }
    </style>
    <script type="text/javascript" charset="utf-8">
        var socket = io();
        var role = "使用者";
        var userName = '';

        document.addEventListener('DOMContentLoaded', function() {
            var nameInput = document.getElementById('nameInput');
            var chatForm = document.getElementById('chatForm');
            var chat = document.getElementById('chat');
            var nameForm = document.getElementById('nameForm');
            var input = document.getElementById('input');

            nameForm.onsubmit = function(e) {
                e.preventDefault();
                if (nameInput.value) {
                    userName = nameInput.value;
                    socket.emit('register user', userName);
                    nameForm.style.display = 'none';
                    chatForm.style.display = 'block';
                }
            };

            chatForm.onsubmit = function(e) {
                e.preventDefault();
                if (input.value) {
                    socket.emit('chat message', {message: input.value, role: role, name: userName});
                    input.value = '';
                }
            };

            socket.on('chat message', function(msg) {
                var item = document.createElement('li');
                var timestamp = document.createElement('span');
                var messageText = document.createTextNode(msg.name + ': ' + msg.message);
        
                item.className = 'list-group-item ' + (msg.role === '使用者' && msg.name === userName ? 'user-message' : 'admin-message');
                timestamp.className = 'timestamp';
                timestamp.textContent = ' 　　' + new Date().toLocaleTimeString();
                
                item.appendChild(messageText);
                item.appendChild(timestamp);
                chat.appendChild(item);
                chat.scrollTop = chat.scrollHeight;
            });
        });
    </script>
</head>
<body>
    <div class="container">
        <form id="nameForm" class="form-inline mt-3 mb-3">
            <input id="nameInput" class="form-control mr-sm-2" type="text" placeholder="輸入您在line的名稱" autocomplete="off">
            <button class="btn btn-primary my-2 my-sm-0" type="submit">發送</button>
        </form>
        <ul id="chat" class="list-group mt-3"></ul>
        <form id="chatForm" class="form-inline mt-3 mb-3" style="display:none;">
            <input id="input" class="form-control mr-sm-2" type="text" autocomplete="off" placeholder="輸入您的問題">
            <button id="sendButton" class="btn btn-success my-2 my-sm-0" type="submit">發送</button>
        </form>
    </div>
</body>
</html>
'''

ADMIN_HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>客服聊天室 - 商家</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <style>
        body {
            background-color: #ececec;
            font-family: Arial, sans-serif;
        }
        #chat {
            margin-bottom: 10px;
            overflow-y: auto;
            height: 400px;
            border: 1px solid #ccc;
            padding: 10px;
            background-color: #ffffff;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .list-group-item {
            background-color: #f8f9fa;
            border: none;
            border-radius: 18px;
            margin-bottom: 10px;
            padding: 10px 20px;
            position: relative;
            display: flex;
            align-items: center;
            max-width: 80%;
            word-wrap: break-word;
            justify-content: space-between;
            align-items: center;
        }
        .list-group-item.user-message {
            background-color: #f0f0f0;
            color: #000;
            margin-right: auto;
            align-self: flex-start;
            text-align: left;
        }

        .list-group-item.admin-message {
            background-color: #d9fdd3;
            color: #000;
            margin-left: auto;
            align-self: flex-end;
            text-align: right;
        }
        .list-group-item.timestamp {
            display: inline-block;
            font-size: 0.8em;
            color: #666;
            margin-left: 10px; /* For space between message and timestamp */
            white-space: nowrap;
            flex-shrink: 0;
        }
        #nameForm, #chatForm {
            margin-top: 20px;
        }
        #input, #nameInput {
            width: 70%;
            margin-right: 10px;
        }
    </style>
    <script type="text/javascript" charset="utf-8">
        var socket = io();
        var role = "四個圈輪業";

        document.addEventListener('DOMContentLoaded', function() {
            var input = document.getElementById('input');
            var form = document.getElementById('form');
            var chat = document.getElementById('chat');
            var user_list = document.getElementById('user_list');

            form.onsubmit = function(e) {
                e.preventDefault();
                if (input.value) {
                    socket.emit('chat message', {message: input.value, role: role});
                    input.value = '';
                }
            };

            socket.on('chat message', function(msg) {
                var item = document.createElement('li');
                var messageContent = document.createElement('span');
                var timestamp = document.createElement('span');

                item.className = 'list-group-item ' + (msg.role === '使用者' ? 'user-message' : 'admin-message');
                messageContent.className = 'message-content';
                messageContent.textContent = msg.name + ' (' + msg.role + '): ' + msg.message;
                
                timestamp.className = 'timestamp';
                timestamp.textContent = ' 　　' + new Date().toLocaleTimeString();

                item.appendChild(messageContent);
                item.appendChild(timestamp);

                chat.appendChild(item);
                chat.scrollTop = chat.scrollHeight;
            });

            socket.on('update_users', function(users) {
                var user_list = document.getElementById('user_list');
                user_list.innerHTML = '<option value="">請選擇用戶</option>';
                users.forEach(function(user) {
                    var option = document.createElement('option');
                    option.textContent = user;
                    option.value = user;
                    user_list.appendChild(option);
                });
            });
        });

        function switchRoom() {
            var user_id = user_list.value;
            socket.emit('switch room', {new_room: user_id});
        }
    </script>
    <script>
        var idleTime = 0;
        var idleInterval = setInterval(timerIncrement, 60000); // 60000 毫秒 = 1 分鐘

        // 用戶活動偵測，每當有活動發生時重置閒置計時器
        document.addEventListener('mousemove', resetTimer, false);
        document.addEventListener('keydown', resetTimer, false);
        document.addEventListener('scroll', resetTimer, false);
        document.addEventListener('touchstart', resetTimer, false);

        function resetTimer() {
            idleTime = 0;
        }

        function timerIncrement() {
            idleTime += 1;
            if (idleTime >= 60) { // 60分鐘
                clearInterval(idleInterval);
                document.getElementById('chat').innerHTML = ''; // 清空聊天內容
                // 如果需要重新整理頁面，取消上面一行的註釋並使用下面這行
                // location.reload();
            }
        }
    </script>
</head>
<body>
    <div class="container">
        <select id="user_list" onchange="switchRoom()" class="form-control mb-3">
        <option value="">請選擇用戶</option>
            <!-- 用戶列表在這裡動態生成 -->
        </select>
        <ul id="chat" class="list-group mt-3"></ul>
        <form id="form" class="form-inline mt-3 mb-3">
            <input id="input" class="form-control mr-sm-2" type="text" autocomplete="off" placeholder="回答問題">
            <button class="btn btn-success my-2 my-sm-0" type="submit">發送</button>
        </form>
    </div>
</body>
</html>
'''


from flask import Flask, render_template_string, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test_secret_key'
socketio = SocketIO(app)

users_rooms = {} 
admin_current_room = {}
room_messages = {}

@app.route('/')
def user():
    return render_template_string(USER_HTML_TEMPLATE)

@app.route('/admin')
def admin():
    return render_template_string(ADMIN_HTML_TEMPLATE)

@socketio.on('connect')
def handle_connect():
    print(f"Connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.sid
    if user_id in users_rooms:
        room_name = users_rooms[user_id]
        leave_room(room_name)
        print(f"{user_id} left room {room_name}")
        del users_rooms[user_id]
        emit('update_users', list(users_rooms.values()), broadcast=True, include_self=False)
    if user_id in admin_current_room:
        del admin_current_room[user_id]

@socketio.on('register user')
def handle_register_user(name):
    user_id = request.sid
    session['name'] = name
    users_rooms[user_id] = name
    join_room(name)
    emit('update_users', list(users_rooms.values()), broadcast=True)

# @socketio.on('switch room')
# def handle_switch_room(data):
#     admin_id = request.sid
#     new_room = data['new_room']
#     if admin_id in admin_current_room:
#         leave_room(admin_current_room[admin_id])
#     join_room(new_room)
#     admin_current_room[admin_id] = new_room
#     emit('chat message', {'role': 'System', 'message': f"您現在正與{new_room}聊天"}, room=admin_id)

# @socketio.on('chat message')
# def handle_message(data):
#     message = data['message']
#     role = data['role']
#     user_id = request.sid
#     if role == '使用者':
#         room_name = users_rooms[user_id]
#     else:
#         if user_id in admin_current_room:
#             room_name = admin_current_room[user_id]
#         else:
#             emit('chat message', {'role': 'System', 'message': '請先選擇一個用戶進行對話。'}, room=user_id)
#             return
#     print(f"Message from {role} ({user_id}) to room {room_name}: {message}")
#     emit('chat message', {'message': message, 'role': role}, room=room_name)

@socketio.on('switch room')
def handle_switch_room(data):
    admin_id = request.sid
    new_room = data['new_room']
    if admin_id in admin_current_room:
        leave_room(admin_current_room[admin_id])
    join_room(new_room)
    admin_current_room[admin_id] = new_room

    if new_room in room_messages:
        for msg in room_messages[new_room]:
            emit('chat message', msg, room=admin_id)

    emit('chat message', {'role': '系統', 'message': f"您現在正與{new_room}聊天", 'name': '四個圈輪業'}, room=admin_id)
    
@socketio.on('chat message')
def handle_message(data):
    message = data['message']
    role = data['role']
    name = data.get('name', '')
    user_id = request.sid
    if role == '使用者':
        room_name = users_rooms[user_id]
        display_name = session.get('name', 'Unknown User')
    else:
        room_name = admin_current_room.get(user_id, '')
        display_name = '商家'

    if room_name not in room_messages:
        room_messages[room_name] = []
    
    room_messages[room_name].append({'role': role, 'message': message, 'name': display_name})

    emit('chat message', {'message': message, 'role': role, 'name': display_name}, room=room_name)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=8080)
