import eventlet
import socketio

def server_main(sio, web_q, player_q):
    app = socketio.WSGIApp(sio, static_files={
        '/': {'content_type': 'text/html', 'filename': 'index.html'}
    })

    @sio.event
    def connect(sid, environ):
        print('connect ', sid)

    @sio.event
    def handshake(sid, data):
        print('handshake message: ', data)
        sio.emit('handshake', 'Hello there from python')

    @sio.event
    def radio(sid, data):
        print('radio message: ', data)
        player_q.put(data)

    @sio.event
    def disconnect(sid):
        print('disconnect ', sid)

    eventlet.wsgi.server(eventlet.listen(('', 8081)), app)
