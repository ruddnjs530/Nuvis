import { Injectable } from '@nestjs/common';
import { PrismaService } from 'src/common/prisma/prisma.service';

@Injectable()
export class RoomConditionHistoryRepository {
  constructor(private readonly prisma: PrismaService) {}

  async create(data: { roomId: number, temperature: number, humidity: number, fineDust: number }) {
    return this.prisma.roomConditionHistory.create({ data });
  }

  async findRecentByUserId(userId: number, days: number = 14) {
    const dateLimit = new Date();
    dateLimit.setDate(dateLimit.getDate() - days);
    
    return this.prisma.roomConditionHistory.findMany({
      where: { 
        room: { userId }, 
        recordedAt: { gte: dateLimit } 
      },
      orderBy: { recordedAt: 'asc' }
    });
  }
}
