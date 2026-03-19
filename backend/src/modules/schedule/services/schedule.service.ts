import { Injectable } from '@nestjs/common';
import { ScheduleRepository } from '../repositories/schedule.repository';

@Injectable()
export class ScheduleService {
  create(data: any): any {
    return { id: 1, ...data };
  }
}
