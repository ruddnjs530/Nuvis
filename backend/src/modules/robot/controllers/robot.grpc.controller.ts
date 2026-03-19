import { Controller } from '@nestjs/common';
import { GrpcMethod } from '@nestjs/microservices';
import { RobotService } from '../services/robot.service';

@Controller()
export class RobotGrpcController {
  constructor(private readonly service: RobotService) {}

  @GrpcMethod('RobotService', 'CreateRobot')
  create(data: any) {
    return this.service.create(data);
  }
}
