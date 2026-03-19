import { Injectable } from '@nestjs/common';
import { EventRepository } from '../repositories/event.repository';

@Injectable()
export class EventService {
  create(data: any): any {
    return { id: 1, ...data };
  }
}
