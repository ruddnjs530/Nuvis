import { Controller, Get, UseGuards } from '@nestjs/common';
import { RoomService } from '../services/room.service';
import { RoomNameListResponseDto } from '../dto/room.dto';
import { RankGuard } from 'src/common/guard/auth.guard';
import { GetUser } from 'src/common/decorator/get-user.decorator';
import { User } from 'src/modules/auth/models/user.model';

@Controller('api/room')
export class RoomController {
  constructor(private readonly roomService: RoomService) {}

  @Get('name')
  @UseGuards(RankGuard)
  async getAllRoomNames(@GetUser() user: User): Promise<RoomNameListResponseDto> {
    return this.roomService.getAllRoomNames(user.userId);
  }
}
