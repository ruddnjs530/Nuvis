import { Module } from '@nestjs/common';
import { RobotModule } from '../robot/robot.module';
import { ScheduleController } from './controllers/schedule.controller';
import { ScheduleGrpcController } from './controllers/schedule.grpc.controller';
import { ScheduleService } from './services/schedule.service';
import { ScheduleRepository } from './repositories/schedule.repository';
import { ScheduleGateway } from './gateways/schedule.gateway';

@Module({
  imports: [RobotModule],
  controllers: [ScheduleController, ScheduleGrpcController],
  providers: [ScheduleService, ScheduleRepository, ScheduleGateway],
  exports: [ScheduleService],
})
export class ScheduleModule {}
