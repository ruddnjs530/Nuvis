import { Injectable } from '@nestjs/common';
import { Room, RoomProps } from '../../../domain/room/room.entity';
import { MapDataVO } from '../../../domain/room/vo/map-data.vo';
import { PrismaService } from '../../../infrastructure/database/prisma/prisma.service';

export interface CreateRoomCommand {
  userId: number;
  name: string;
  mapData?: any;
}

@Injectable()
export class CreateRoomUseCase {
  constructor(private readonly prisma: PrismaService) {}

  async execute(command: CreateRoomCommand): Promise<Room> {
    const mapData = MapDataVO.create(command.mapData || null);

    const roomProps: RoomProps = {
      userId: command.userId,
      name: command.name,
      mapData,
    };
    
    const room = Room.create(null, roomProps);

    const savedRecord = await this.prisma.room.create({
      data: {
        userId: room.userId,
        name: room.name,
        mapData: room.mapData?.value || null,
      },
    });

    return Room.create(savedRecord.roomId, {
      userId: savedRecord.userId,
      name: savedRecord.name,
      mapData: MapDataVO.create(savedRecord.mapData),
    });
  }
}
