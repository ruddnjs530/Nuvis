import { Injectable } from '@nestjs/common';
import { RoomRepository } from '../repositories/room.repository';

@Injectable()
export class RoomService {
  constructor(private readonly roomRepository: RoomRepository) {}
}
