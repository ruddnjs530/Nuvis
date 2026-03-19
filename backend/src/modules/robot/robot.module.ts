import { Module } from '@nestjs/common';
import { RobotController } from './controllers/robot.controller';
import { RobotGrpcController } from './controllers/robot.grpc.controller';
import { RobotService } from './services/robot.service';
import { RobotRepository } from './repositories/robot.repository';
import { RobotGateway } from './gateways/robot.gateway';

@Module({
  controllers: [RobotController, RobotGrpcController],
  providers: [RobotService, RobotRepository, RobotGateway],
  exports: [RobotService],
})
export class RobotModule {}
