import { Module } from '@nestjs/common';
import { RoomController } from './controllers/room.controller';
// import { RoomGrpcController } from './controllers/room.grpc.controller';
import { RoomService } from './services/room.service';
import { RoomRepository } from './repositories/room.repository';
import { RoomConditionHistoryRepository } from './repositories/room-condition-history.repository';
import { RoomGateway } from './gateways/room.gateway';

@Module({
  controllers: [RoomController /*, RoomGrpcController*/],
  providers: [RoomService, RoomRepository, RoomConditionHistoryRepository, RoomGateway],
  exports: [RoomService, RoomConditionHistoryRepository],
})
export class RoomModule {}
