import { WebSocketGateway, SubscribeMessage, MessageBody, WebSocketServer } from '@nestjs/websockets';
import { Server } from 'socket.io';
import { ScheduleService } from '../services/schedule.service';

@WebSocketGateway({ cors: true, namespace: 'schedule' })
export class ScheduleGateway {
  @WebSocketServer()
  server: Server;

  constructor(private readonly service: ScheduleService) {}

  @SubscribeMessage('create')
  async handleCreate(@MessageBody() data: any): Promise<string> {
    // Mock user 1 for dummy WS call
    const item = await this.service.create(1, data);
    this.server.emit('created', item);
    return 'Created';
  }
}
