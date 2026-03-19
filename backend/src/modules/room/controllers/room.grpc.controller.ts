import { Controller } from '@nestjs/common';
import { GrpcMethod } from '@nestjs/microservices';
import { RoomService } from '../services/room.service';

@Controller()
export class RoomGrpcController {
  constructor(private readonly service: RoomService) {}

  @GrpcMethod('RoomService', 'CreateRoom')
  create(data: any) {
    return this.service.create(data);
  }
}
