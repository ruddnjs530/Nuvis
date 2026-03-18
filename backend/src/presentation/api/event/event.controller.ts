import { Controller, Post, Body, HttpCode, HttpStatus } from '@nestjs/common';
import { CreateEventUseCase } from '../../../application/event/usecases/create-event.usecase';
import { CreateEventDto } from './dto/create-event.dto';

@Controller('events')
export class EventController {
  constructor(private readonly createEventUseCase: CreateEventUseCase) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  async createEvent(@Body() createEventDto: CreateEventDto) {
    const event = await this.createEventUseCase.execute({
      userId: createEventDto.userId,
      roomId: createEventDto.roomId,
      conditionType: createEventDto.conditionType,
      conditionOperator: createEventDto.conditionOperator,
      thresholdValue: createEventDto.thresholdValue,
      actionModuleType: createEventDto.actionModuleType,
    });

    return {
      message: 'Event created successfully',
      data: {
        id: event.id,
        userId: event.userId,
        roomId: event.roomId,
        conditionType: event.conditionType,
        conditionOperator: event.conditionOperator,
        thresholdValue: event.threshold.value,
        actionModuleType: event.actionModuleType,
        isActive: event.isActive,
      },
    };
  }
}
