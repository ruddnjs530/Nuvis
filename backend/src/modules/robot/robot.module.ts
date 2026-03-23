import { Module, forwardRef } from '@nestjs/common';
import { RoomModule } from '../room/room.module';
import { RobotController } from './controllers/robot.controller';
import { RobotGrpcController } from './controllers/robot.grpc.controller';
import { RobotService } from './services/robot.service';
import { RobotRepository } from './repositories/robot.repository';
import { ModuleControlLogRepository } from './repositories/module-control-log.repository';
import { RobotGateway } from './gateways/robot.gateway';

@Module({
  imports: [forwardRef(() => RoomModule)],
  controllers: [RobotController, RobotGrpcController],
  providers: [RobotService, RobotRepository, ModuleControlLogRepository, RobotGateway],
  exports: [RobotService, ModuleControlLogRepository],
})
export class RobotModule {}

