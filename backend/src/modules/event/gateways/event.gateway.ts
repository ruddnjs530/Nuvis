import { WebSocketGateway, SubscribeMessage, MessageBody, WebSocketServer } from '@nestjs/websockets';
import { Server } from 'socket.io';
import { EventService } from '../services/event.service';

@WebSocketGateway({ cors: true, namespace: 'event' })
export class EventGateway {
  @WebSocketServer()
  server: Server;

  constructor(private readonly service: EventService) {}

  // @SubscribeMessage('create')
  // handleCreate(@MessageBody() data: any): string {
  //   const item = this.service.create(data);
  //   this.server.emit('created', item);
  //   return 'Created';
  // }
}
