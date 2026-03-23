import { Controller } from '@nestjs/common';
import { ScheduleService } from '../services/schedule.service';

@Controller('api/schedule')
export class ScheduleController {
  constructor(private readonly scheduleService: ScheduleService) {}
}
