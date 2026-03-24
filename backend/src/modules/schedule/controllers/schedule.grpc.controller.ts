import { Controller } from '@nestjs/common';
import { GrpcMethod } from '@nestjs/microservices';
import { ScheduleService } from '../services/schedule.service';

@Controller()
export class ScheduleGrpcController {
  constructor(private readonly service: ScheduleService) {}

  @GrpcMethod('ScheduleService', 'CreateSchedule')
  create(data: any) {
    // Mock user 1 for dummy gRPC call to bypass TS error
    return this.service.create(1, data);
  }
}
