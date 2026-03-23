import { Controller } from '@nestjs/common';
import { GrpcMethod } from '@nestjs/microservices';
import { RobotService } from '../services/robot.service';

@Controller()
export class RobotGrpcController {
  constructor(private readonly service: RobotService) {}

  @GrpcMethod('RobotGateway', 'ExecuteTask')
  executeTask(data: any) {
    return this.service.executeTask(data);
  }

  @GrpcMethod('RobotGateway', 'CancelTask')
  cancelTask(data: any) {
    return this.service.cancelTask(data);
  }

  @GrpcMethod('RobotGateway', 'EmergencyStop')
  emergencyStop(data: any) {
    return this.service.emergencyStop(data);
  }

  @GrpcMethod('RobotGateway', 'ManualControl')
  manualControl(data: any) {
    return this.service.manualControl(data);
  }

  @GrpcMethod('RobotGateway', 'GetStatus')
  getStatus(data: any) {
    return this.service.getStatus();
  }

  @GrpcMethod('RobotGateway', 'StreamStatus')
  streamStatus(data: { interval_ms: number }) {
    return this.service.streamStatus(data.interval_ms);
  }
}
