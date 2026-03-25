import { ApiProperty } from '@nestjs/swagger';

export class ResponseEventDto {
  @ApiProperty({ description: '이벤트 규칙 ID', example: 1 })
  eventId: number;

  @ApiProperty({ description: '유저 ID', example: 1 })
  userId: number;

  @ApiProperty({ description: '방 ID', example: 1 })
  roomId: number;

  @ApiProperty({ description: '조건 종류', example: 'FINE_DUST' })
  conditionType: string;

  @ApiProperty({ description: '조건 연산자', example: 'GT' })
  conditionOperator: string;

  @ApiProperty({ description: '조건 임계값', example: 100 })
  thresholdValue: number;

  @ApiProperty({ description: '실행 대상 모듈 타입', example: 'AIR_PURIFIER' })
  actionModuleType: string;

  @ApiProperty({ description: '모듈 전원 상태 제어 (true: 켜기, false: 끄기)', example: true })
  actionModulePower: boolean;

  @ApiProperty({ description: '모듈 작동 세기/레벨', example: 1 })
  actionModuleLevel: number;

  @ApiProperty({ description: '이벤트의 활성화 여부', example: true })
  isActive: boolean;
}

export class ResponseEventSingleDto {
  @ApiProperty({ type: ResponseEventDto })
  data: ResponseEventDto;
}

export class ResponseEventListDto {
  @ApiProperty({ type: [ResponseEventDto] })
  data: ResponseEventDto[];
}
