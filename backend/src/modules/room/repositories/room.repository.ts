import { Injectable } from '@nestjs/common';
import { PrismaService } from 'src/common/prisma/prisma.service';

@Injectable()
export class RoomRepository {
  constructor(private readonly prismaService: PrismaService) {}

  async findAllNames(userId: number) {
    return this.prismaService.room.findMany({
      where: { userId },
      select: {
        roomId: true,
        name: true,
      },
      orderBy: { roomId: 'asc' },
    });
  }
}
