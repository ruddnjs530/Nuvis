import { Injectable } from '@nestjs/common';
import { RoomRepository } from '../repositories/room.repository';

@Injectable()
export class RoomService {
  create(data: any): any {
    return { id: 1, ...data };
  }
}
