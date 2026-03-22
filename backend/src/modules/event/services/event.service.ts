import { Injectable } from '@nestjs/common';
import { EventRepository } from '../repositories/event.repository';

@Injectable()
export class EventService {
  constructor(private readonly eventRepository: EventRepository) {}

  create(data: any) {
    // Skeleton method added to pass compilation
    return { ...data, createdAt: new Date() };
  }
}
