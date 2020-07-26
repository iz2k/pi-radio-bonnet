import { Injectable } from '@angular/core';
import * as io from 'socket.io-client';

@Injectable({
  providedIn: 'root'
})
export class SocketioService {
  socket;

  public status = 0;
  public icresult;

  constructor() {   }

  private greeting = 'Hello there from Angular!';

  setupSocketConnection(): void {
    //this.socket = io('http://' + window.location.hostname + ':8081');
    this.socket = io('http://raspberrypi:8081/');

    this.socket.on('connect', () => {
      console.log('JS socket connected. Sending greeting.');
      this.socket.emit('handshake', this.greeting);
      this.status = 0;
    });

    this.socket.on('disconnect', () => {
      console.log('JS socket disconnected');
      this.status = 1;
    });

    this.socket.on('handshake', (data: string) => {
      console.log('Handshake received: ' + data);
    });

    this.socket.on('radio', (data: string) => {
      console.log('radio received: ' + data);
    });


  }
}
