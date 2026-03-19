import { Controller } from '@nestjs/common';
import { GrpcMethod } from '@nestjs/microservices';
import { EventService } from '../services/event.service';

@Controller()
export class EventGrpcController {
  constructor(private readonly service: EventService) {}

  @GrpcMethod('EventService', 'CreateEvent')
  create(data: any) {
    return this.service.create(data);
  }
}
