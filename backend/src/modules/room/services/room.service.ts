import { Injectable } from '@nestjs/common';
import { RoomNameListResponseDto } from '../dto/room.dto';
import { RoomRepository } from '../repositories/room.repository';

@Injectable()
export class RoomService {
  constructor(private readonly roomRepository: RoomRepository) {}

  async getAllRoomNames(userId: number): Promise<RoomNameListResponseDto> {
    const rooms = await this.roomRepository.findAllNames(userId);
    return { data: rooms };
  }
}
