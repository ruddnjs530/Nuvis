import { Injectable } from '@nestjs/common';
import { RoomRepository } from '../repositories/room.repository';

@Injectable()
export class RoomService {
  constructor(private readonly roomRepository: RoomRepository) {}

  create(data: any) {
    // Skeleton method added to pass compilation
    return { ...data, createdAt: new Date() };
  }
}
