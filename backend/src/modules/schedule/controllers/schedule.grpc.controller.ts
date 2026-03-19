import { Controller } from '@nestjs/common';
import { GrpcMethod } from '@nestjs/microservices';
import { ScheduleService } from '../services/schedule.service';

@Controller()
export class ScheduleGrpcController {
  constructor(private readonly service: ScheduleService) {}

  @GrpcMethod('ScheduleService', 'CreateSchedule')
  create(data: any) {
    return this.service.create(data);
  }
}
