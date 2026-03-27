import { Injectable } from '@nestjs/common';
import { PrismaService } from 'src/common/prisma/prisma.service';

@Injectable()
export class ScheduleRepository {
  constructor(private readonly prismaService: PrismaService) {}

  /** room relation 포함 조회 (targetZone 사용을 위해) */
  private readonly includeRoom = { room: true } as const;

  async findAllByUserId(userId: number) {
    return this.prismaService.schedule.findMany({
      where: { userId },
      include: this.includeRoom,
    });
  }

  /** 서버 재시작 시 CronJob 복원용 — isActive인 스케줄 전부 조회 */
  async findAllActive() {
    return this.prismaService.schedule.findMany({
      where: { isActive: true },
      include: this.includeRoom,
    });
  }

  async findById(scheduleId: number) {
    return this.prismaService.schedule.findUnique({
      where: { scheduleId },
      include: this.includeRoom,
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
      include: this.includeRoom,
    });
  }

  async update(scheduleId: number, data: any) {
    const updateData: any = { ...data };
    if (data.startTime) updateData.startTime = new Date(data.startTime);
    return this.prismaService.schedule.update({
      where: { scheduleId },
      data: updateData,
      include: this.includeRoom,
    });
  }

  async delete(scheduleId: number) {
    return this.prismaService.schedule.delete({
      where: { scheduleId },
    });
  }
}
