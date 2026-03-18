import {
  WebSocketGateway,
  WebSocketServer,
  SubscribeMessage,
  MessageBody,
  ConnectedSocket,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';

/**
 * Controller for WebRTC Signaling in the Presentation layer.
 */
@WebSocketGateway({ cors: true, namespace: '/webrtc' })
export class WebRtcSignalingGateway {
  @WebSocketServer()
  server: Server;

  @SubscribeMessage('offer')
  handleOffer(
    @MessageBody() data: any,
    @ConnectedSocket() client: Socket,
  ) {
    client.broadcast.emit('offer', data);
  }

  @SubscribeMessage('answer')
  handleAnswer(
    @MessageBody() data: any,
    @ConnectedSocket() client: Socket,
  ) {
    client.broadcast.emit('answer', data);
  }

  @SubscribeMessage('ice-candidate')
  handleIceCandidate(
    @MessageBody() data: any,
    @ConnectedSocket() client: Socket,
  ) {
    client.broadcast.emit('ice-candidate', data);
  }
}
