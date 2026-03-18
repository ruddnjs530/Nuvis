import { Controller, Post, Body, HttpCode, HttpStatus } from '@nestjs/common';
import { CreateRoomUseCase } from '../../../application/room/usecases/create-room.usecase';
import { CreateRoomDto } from './dto/create-room.dto';

@Controller('rooms')
export class RoomController {
  constructor(private readonly createRoomUseCase: CreateRoomUseCase) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  async createRoom(@Body() createRoomDto: CreateRoomDto) {
    const room = await this.createRoomUseCase.execute({
      userId: createRoomDto.userId,
      name: createRoomDto.name,
      mapData: createRoomDto.mapData,
    });

    return {
      message: 'Room created successfully',
      data: {
        id: room.id,
        userId: room.userId,
        name: room.name,
        mapData: room.mapData?.value || null,
      },
    };
  }
}
