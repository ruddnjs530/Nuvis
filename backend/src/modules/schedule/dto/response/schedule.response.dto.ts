import { ApiProperty } from '@nestjs/swagger';

export class ResponseScheduleDto {
  @ApiProperty({ example: 1 })
  scheduleId: number;

  @ApiProperty({ example: 1 })
  userId: number;

  @ApiProperty({ example: 2 })
  roomId: number;

  @ApiProperty({ example: 'AIR_PURIFIER' })
  actionModuleType: string;

  @ApiProperty({ example: true })
  actionModulePower: boolean;

  @ApiProperty({ example: 2 })
  actionModuleLevel: number;

  @ApiProperty({ example: '1970-01-01T14:30:00.000Z' })
  startTime: string;

  @ApiProperty({ example: 60 })
  durationMinutes: number;

  @ApiProperty({ example: true })
  isActive: boolean;
}

export class ResponseScheduleListDto {
  @ApiProperty({ description: '스케줄 목록', type: [ResponseScheduleDto] })
  data: ResponseScheduleDto[];
}
