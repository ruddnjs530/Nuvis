import { Module } from '@nestjs/common';
import { RoomController } from './controllers/room.controller';
import { RoomGrpcController } from './controllers/room.grpc.controller';
import { RoomService } from './services/room.service';
import { RoomRepository } from './repositories/room.repository';
<<<<<<< HEAD
import { RoomConditionHistoryRepository } from './repositories/room-condition-history.repository';
=======
>>>>>>> origin/infra/task/ci-cd-setup
import { RoomGateway } from './gateways/room.gateway';

@Module({
  controllers: [RoomController, RoomGrpcController],
<<<<<<< HEAD
  providers: [RoomService, RoomRepository, RoomConditionHistoryRepository, RoomGateway],
  exports: [RoomService, RoomConditionHistoryRepository],
})
export class RoomModule {}

=======
  providers: [RoomService, RoomRepository, RoomGateway],
  exports: [RoomService],
})
export class RoomModule {}
>>>>>>> origin/infra/task/ci-cd-setup
