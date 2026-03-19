import { WebSocketGateway, SubscribeMessage, MessageBody, WebSocketServer } from '@nestjs/websockets';
import { Server } from 'socket.io';
import { RobotService } from '../services/robot.service';

@WebSocketGateway({ cors: true, namespace: 'robot' })
export class RobotGateway {
  @WebSocketServer()
  server: Server;

  constructor(private readonly service: RobotService) {}

  @SubscribeMessage('create')
  handleCreate(@MessageBody() data: any): string {
    const item = this.service.create(data);
    this.server.emit('created', item);
    return 'Created';
  }
}
