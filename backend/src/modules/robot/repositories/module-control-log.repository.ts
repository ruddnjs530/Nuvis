import { Injectable } from '@nestjs/common';
import { PrismaService } from 'src/common/prisma/prisma.service';

@Injectable()
export class ModuleControlLogRepository {
  constructor(private readonly prisma: PrismaService) {}

  async create(data: { userId: number, moduleId: number, actionModuleType: string, action: string, triggeredBy: string }) {
    return this.prisma.moduleControlLog.create({ data });
  }

  async findRecentByUserId(userId: number, days: number = 14) {
    const dateLimit = new Date();
    dateLimit.setDate(dateLimit.getDate() - days);
    
    return this.prisma.moduleControlLog.findMany({
      where: { 
        userId, 
        createdAt: { gte: dateLimit } 
      },
      orderBy: { createdAt: 'asc' }
    });
  }
}
