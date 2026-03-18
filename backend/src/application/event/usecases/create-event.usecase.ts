import { Injectable } from '@nestjs/common';
import { Event, EventProps } from '../../../domain/event/event.entity';
import { ThresholdVO } from '../../../domain/event/vo/threshold.vo';
import { PrismaService } from '../../../infrastructure/database/prisma/prisma.service';

export interface CreateEventCommand {
  userId: number;
  roomId: number;
  conditionType: string;
  conditionOperator: string;
  thresholdValue: number;
  actionModuleType: string;
}

@Injectable()
export class CreateEventUseCase {
  constructor(private readonly prisma: PrismaService) {}

  async execute(command: CreateEventCommand): Promise<Event> {
    const threshold = ThresholdVO.create(command.thresholdValue);

    const eventProps: EventProps = {
      userId: command.userId,
      roomId: command.roomId,
      conditionType: command.conditionType,
      conditionOperator: command.conditionOperator,
      threshold,
      actionModuleType: command.actionModuleType,
      isActive: true, // Default active on creation
    };

    const event = Event.create(null, eventProps);

    const savedRecord = await this.prisma.event.create({
      data: {
        userId: event.userId,
        roomId: event.roomId,
        conditionType: event.conditionType,
        conditionOperator: event.conditionOperator,
        thresholdValue: event.threshold.value,
        actionModuleType: event.actionModuleType,
        isActive: event.isActive,
      },
    });

    return Event.create(savedRecord.eventId, {
      userId: savedRecord.userId,
      roomId: savedRecord.roomId,
      conditionType: savedRecord.conditionType,
      conditionOperator: savedRecord.conditionOperator,
      threshold: ThresholdVO.create(savedRecord.thresholdValue),
      actionModuleType: savedRecord.actionModuleType,
      isActive: savedRecord.isActive,
    });
  }
}
