import { Component } from '@angular/core';
import {SocketioService} from './socketio.service';
import {NgxSpinnerService} from "ngx-spinner";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  constructor(public socketService: SocketioService, private spinner: NgxSpinnerService) {}

  ngOnInit(): void {
    this.socketService.setupSocketConnection();
    this.spinner.show();
  }

  updateSetting(event): void {
    //console.log('SetVol: ', event.value);
    this.socketService.socket.emit('radio', ['vol', event.value]);
  }

  volUp(event: Event): void {
    //console.log('VolUp!', event);
    this.socketService.socket.emit('radio', ['vol_up', 0]);
  }
  volDown(event: Event): void {
    //console.log('VolDown!', event);
    this.socketService.socket.emit('radio', ['vol_down', 0]);
  }
  seekUp(event: Event): void {
    //console.log('SeekUp!', event);
    this.socketService.socket.emit('radio', ['seek_up', 0]);
  }
  seekDown(event: Event): void {
    //console.log('SeekDown!', event);
    this.socketService.socket.emit('radio', ['seek_down', 0]);
  }
}
