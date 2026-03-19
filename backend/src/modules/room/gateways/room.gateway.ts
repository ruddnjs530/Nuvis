import { WebSocketGateway, SubscribeMessage, MessageBody, WebSocketServer } from '@nestjs/websockets';
import { Server } from 'socket.io';
import { RoomService } from '../services/room.service';

@WebSocketGateway({ cors: true, namespace: 'room' })
export class RoomGateway {
  @WebSocketServer()
  server: Server;

  constructor(private readonly service: RoomService) {}

  @SubscribeMessage('create')
  handleCreate(@MessageBody() data: any): string {
    const item = this.service.create(data);
    this.server.emit('created', item);
    return 'Created';
  }
}
