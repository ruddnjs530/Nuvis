import { Module } from '@nestjs/common';
import { ScheduleController } from './schedule.controller';
import { CreateScheduleUseCase } from '../../../application/schedule/usecases/create-schedule.usecase';
import { PrismaModule } from '../../../infrastructure/database/prisma/prisma.module';

@Module({
  imports: [PrismaModule],
  controllers: [ScheduleController],
  providers: [CreateScheduleUseCase],
  exports: [CreateScheduleUseCase],
})
export class ScheduleApiModule {}
