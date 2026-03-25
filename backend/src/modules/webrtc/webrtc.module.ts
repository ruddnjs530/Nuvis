import { Module } from '@nestjs/common';
import { WebrtcSignalingController } from './controllers/webrtc-signaling.controller';
import { WebrtcSignalingService } from './services/webrtc-signaling.service';

@Module({
  controllers: [WebrtcSignalingController],
  providers: [WebrtcSignalingService],
})
export class WebrtcModule {}
