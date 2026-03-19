import { Injectable } from '@nestjs/common';
import { EventRepository } from '../repositories/event.repository';

@Injectable()
export class EventService {
  constructor(private readonly eventRepository: EventRepository) {}
}
