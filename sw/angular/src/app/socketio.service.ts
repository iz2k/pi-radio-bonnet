import { Injectable } from '@angular/core';
import * as io from 'socket.io-client';

@Injectable({
  providedIn: 'root'
})
export class SocketioService {
  public socket;
  public volume;
  public radio;
  public connectedToServer = false;

  constructor() {   }

  setupSocketConnection(): void {
    console.log('Setting up socket connection...')
    this.socket = io('http://' + window.location.hostname + ':8081');
    //this.socket = io('http://raspberrypi:8081/');

    this.socket.on('connect', () => {
      console.log('Socket connected.');
      this.connectedToServer = true;
    });

    this.socket.on('disconnect', () => {
      console.log('Socket disconnected');
      this.connectedToServer = false;
    });

    this.socket.on('volume', (data: bigint) => {
      this.volume = data;
      //console.log('Volume received: ' + data);
    });

    this.socket.on('radio', (data: object) => {
      this.radio = data;
      //console.log('Radio received: ' + data);
    });

  }
}
