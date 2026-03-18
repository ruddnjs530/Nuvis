import { Controller, Post, Body, HttpCode, HttpStatus } from '@nestjs/common';
import { CreateScheduleUseCase } from '../../../application/schedule/usecases/create-schedule.usecase';
import { CreateScheduleDto } from './dto/create-schedule.dto';

@Controller('schedules')
export class ScheduleController {
  constructor(private readonly createScheduleUseCase: CreateScheduleUseCase) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  async createSchedule(@Body() createScheduleDto: CreateScheduleDto) {
    const schedule = await this.createScheduleUseCase.execute({
      userId: createScheduleDto.userId,
      roomId: createScheduleDto.roomId,
      actionModuleType: createScheduleDto.actionModuleType,
      startTime: createScheduleDto.startTime,
      durationMinutes: createScheduleDto.durationMinutes,
    });

    return {
      message: 'Schedule created successfully',
      data: {
        id: schedule.id,
        userId: schedule.userId,
        roomId: schedule.roomId,
        actionModuleType: schedule.actionModuleType,
        startTime: schedule.startTime,
        durationMinutes: schedule.duration.value,
        isActive: schedule.isActive,
      },
    };
  }
}
