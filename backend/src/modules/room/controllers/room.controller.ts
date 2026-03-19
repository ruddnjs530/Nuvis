import { Controller } from '@nestjs/common';
import { RoomService } from '../services/room.service';

@Controller('room')
export class RoomController {
  constructor(private readonly roomService: RoomService) {}
}
