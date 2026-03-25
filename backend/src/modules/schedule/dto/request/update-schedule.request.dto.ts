import { PartialType } from '@nestjs/swagger';
import { CreateScheduleDto } from './create-schedule.request.dto';

export class UpdateScheduleDto extends PartialType(CreateScheduleDto) {}
