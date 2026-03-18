import { Module } from '@nestjs/common';
import { RoomController } from './room.controller';
import { CreateRoomUseCase } from '../../../application/room/usecases/create-room.usecase';
import { PrismaModule } from '../../../infrastructure/database/prisma/prisma.module';

@Module({
  imports: [PrismaModule],
  controllers: [RoomController],
  providers: [CreateRoomUseCase],
  exports: [CreateRoomUseCase],
})
export class RoomApiModule {}
