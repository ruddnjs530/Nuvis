import { Module } from '@nestjs/common';
import { RobotModule } from '../robot/robot.module';
import { RoomModule } from '../room/room.module';
import { EventController } from './controllers/event.controller';
import { EventGrpcController } from './controllers/event.grpc.controller';
import { EventService } from './services/event.service';
import { EventRepository } from './repositories/event.repository';
import { EventGateway } from './gateways/event.gateway';

@Module({
  imports: [RobotModule, RoomModule],
  controllers: [EventController, EventGrpcController],
  providers: [EventService, EventRepository, EventGateway],
  exports: [EventService],
})
export class EventModule {}
