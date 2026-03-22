import { Injectable } from '@nestjs/common';
import { ScheduleRepository } from '../repositories/schedule.repository';

@Injectable()
export class ScheduleService {
  constructor(private readonly scheduleRepository: ScheduleRepository) {}

  create(data: any) {
    // Skeleton method added to pass compilation
    return { ...data, createdAt: new Date() };
  }
}
