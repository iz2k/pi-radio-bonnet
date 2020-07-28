from flask import send_from_directory

def define_webserver(player_q):
    import eventlet

    # Monkey_Patch eventlet to support threads
    eventlet.monkey_patch()

    from flask import Flask, render_template, session, request
    from flask_socketio import SocketIO

    # Create Flask_SocketIO App
    app = Flask(__name__, static_url_path='/web')
    app.config['SECRET_KEY'] = 'secret!'
    sio = SocketIO(app, async_mode='eventlet')
    sio.init_app(app, cors_allowed_origins="*")

    @app.route('/')
    def root():
        print('Serving angular frontend...')
        return send_from_directory('web/', 'index.html')


    @sio.on('connect')
    def onconnect_event():
        print('Web Player instance connected!')

    @sio.on('disconnect')
    def onconnect_event():
        print('Web Player instance disconnected!')

    # Custom event
    @sio.on('radio')
    def handle_radio(data, methods=['GET', 'POST']):
        #print('Radio received: ' + str(data))
        player_q.put(data)

    return [app, sio]
