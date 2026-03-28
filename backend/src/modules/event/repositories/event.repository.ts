import { Injectable } from '@nestjs/common';
import { PrismaService } from 'src/common/prisma/prisma.service';

@Injectable()
export class EventRepository {
  constructor(private readonly prisma: PrismaService) {}

  async findAll(userId: number) {
    return this.prisma.event.findMany({
      where: { userId },
      include: { room: true },
    });
  }

  async findActiveEvents() {
    return this.prisma.event.findMany({
      where: { isActive: true },
      include: { room: true },
    });
  }

  async create(userId: number, data: any) {
    return this.prisma.event.create({
      data: {
        ...data,
        userId,
      },
      include: { room: true },
    });
  }

  async update(eventId: number, userId: number, data: any) {
    return this.prisma.event.update({
      where: { eventId, userId },
      data,
      include: { room: true },
    });
  }

  async delete(eventId: number, userId: number) {
    return this.prisma.event.delete({
      where: { eventId, userId },
    });
  }
}
