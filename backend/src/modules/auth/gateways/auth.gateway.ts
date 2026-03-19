import { WebSocketGateway, SubscribeMessage, MessageBody, WebSocketServer } from '@nestjs/websockets';
import { Server } from 'socket.io';
import { AuthService } from '../services/auth.service';


@WebSocketGateway({ cors: true, namespace: 'auth' })
export class AuthGateway {
  @WebSocketServer()
  server: Server;

  constructor(private readonly service: AuthService) {}


}
