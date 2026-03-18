import { Injectable } from '@nestjs/common';
import { Schedule, ScheduleProps } from '../../../domain/schedule/schedule.entity';
import { DurationVO } from '../../../domain/schedule/vo/duration.vo';
import { PrismaService } from '../../../infrastructure/database/prisma/prisma.service';

export interface CreateScheduleCommand {
  userId: number;
  roomId: number;
  actionModuleType: string;
  startTime: string; // ISO string format preferred for DB time objects
  durationMinutes: number;
}

@Injectable()
export class CreateScheduleUseCase {
  constructor(private readonly prisma: PrismaService) {}

  async execute(command: CreateScheduleCommand): Promise<Schedule> {
    const duration = DurationVO.create(command.durationMinutes);
    const parsedTime = new Date(command.startTime); // Expecting parsable DateTime or Time

    const scheduleProps: ScheduleProps = {
      userId: command.userId,
      roomId: command.roomId,
      actionModuleType: command.actionModuleType,
      startTime: parsedTime,
      duration,
      isActive: true, // Default to true on creation
    };

    const schedule = Schedule.create(null, scheduleProps);

    const savedRecord = await this.prisma.schedule.create({
      data: {
        userId: schedule.userId,
        roomId: schedule.roomId,
        actionModuleType: schedule.actionModuleType,
        startTime: schedule.startTime,
        durationMinutes: schedule.duration.value,
        isActive: schedule.isActive,
      },
    });

    return Schedule.create(savedRecord.scheduleId, {
      userId: savedRecord.userId,
      roomId: savedRecord.roomId,
      actionModuleType: savedRecord.actionModuleType,
      startTime: savedRecord.startTime,
      duration: DurationVO.create(savedRecord.durationMinutes),
      isActive: savedRecord.isActive,
    });
  }
}
