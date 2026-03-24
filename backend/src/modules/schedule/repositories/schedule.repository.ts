import { Injectable } from '@nestjs/common';
import { PrismaService } from 'src/common/prisma/prisma.service';

@Injectable()
export class ScheduleRepository {
  constructor(private readonly prismaService: PrismaService) {}

  async findAllByUserId(userId: number) {
    return this.prismaService.schedule.findMany({
      where: { userId },
    });
  }

  async findById(scheduleId: number) {
    return this.prismaService.schedule.findUnique({
      where: { scheduleId },
    });
  }

  async create(userId: number, data: any) {
    return this.prismaService.schedule.create({
      data: {
        userId,
        roomId: data.roomId,
        actionModuleType: data.actionModuleType,
        actionModulePower: data.actionModulePower ?? true,
        actionModuleLevel: data.actionModuleLevel ?? 1,
        startTime: new Date(data.startTime),
        durationMinutes: data.durationMinutes,
        isActive: data.isActive,
      },
    });
  }

  async update(scheduleId: number, data: any) {
    const updateData: any = { ...data };
    if (data.startTime) updateData.startTime = new Date(data.startTime);
    return this.prismaService.schedule.update({
      where: { scheduleId },
      data: updateData,
    });
  }

  async delete(scheduleId: number) {
    return this.prismaService.schedule.delete({
      where: { scheduleId },
    });
  }
}
