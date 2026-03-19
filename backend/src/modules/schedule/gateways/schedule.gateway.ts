import { WebSocketGateway, SubscribeMessage, MessageBody, WebSocketServer } from '@nestjs/websockets';
import { Server } from 'socket.io';
import { ScheduleService } from '../services/schedule.service';

@WebSocketGateway({ cors: true, namespace: 'schedule' })
export class ScheduleGateway {
  @WebSocketServer()
  server: Server;

  constructor(private readonly service: ScheduleService) {}

  @SubscribeMessage('create')
  handleCreate(@MessageBody() data: any): string {
    const item = this.service.create(data);
    this.server.emit('created', item);
    return 'Created';
  }
}
