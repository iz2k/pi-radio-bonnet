import { Component } from '@angular/core';
import {SocketioService} from './socketio.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'angular';

  constructor(public socketService: SocketioService) {}

  ngOnInit(): void {
    this.socketService.setupSocketConnection();
    console.log('algo!');
  }
  handleClick(event: Event): void {
    console.log('Click!', event);
    this.socketService.socket.emit('handshake', 'kkmendra');
  }
  volUp(event: Event): void {
    console.log('VolUp!', event);
    this.socketService.socket.emit('radio', 'vol_up');
  }
  volDown(event: Event): void {
    console.log('VolUp!', event);
    this.socketService.socket.emit('radio', 'vol_down');
  }
  seekUp(event: Event): void {
    console.log('VolUp!', event);
    this.socketService.socket.emit('radio', 'seek_up');
  }
  seekDown(event: Event): void {
    console.log('VolUp!', event);
    this.socketService.socket.emit('radio', 'seek_down');
  }
}
