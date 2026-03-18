import { Module } from '@nestjs/common';
import { EventController } from './event.controller';
import { CreateEventUseCase } from '../../../application/event/usecases/create-event.usecase';
import { PrismaModule } from '../../../infrastructure/database/prisma/prisma.module';

@Module({
  imports: [PrismaModule],
  controllers: [EventController],
  providers: [CreateEventUseCase],
  exports: [CreateEventUseCase],
})
export class EventApiModule {}
