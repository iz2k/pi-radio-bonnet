from flask import send_from_directory

def define_webserver(player_q):
    import eventlet

    # Monkey_Patch eventlet to support threads
    eventlet.monkey_patch()

    from flask import Flask, render_template, session, request
    from flask_socketio import SocketIO

    # Create Flask_SocketIO App
    app = Flask(__name__, static_url_path='')
    app.config['SECRET_KEY'] = 'secret!'
    sio = SocketIO(app, async_mode='eventlet')
    sio.init_app(app, cors_allowed_origins="*")

    @app.route('/')
    def root():
        print('accessing root')
        return send_from_directory('web/', 'index.html')


    @sio.on('connect')
    def onconnect_event():
        print('Client connected!')

    @sio.on('disconnect')
    def onconnect_event():
        print('Client disconnected!')

    # Custom event
    @sio.on('handshake')
    def handle_handshake(data, methods=['GET', 'POST']):
        print('Handshake received: ' + str(data))
        print('Sending greeting.')
        sio.emit('handshake', 'Hello there from Flask!')

    # Custom event
    @sio.on('radio')
    def handle_radio(data, methods=['GET', 'POST']):
        print('Radio received: ' + str(data))
        player_q.put(data)

    return [app, sio]

def shutdown_server():
    from flask import request
    print('shutdown server')
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
