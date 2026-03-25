import { IsBoolean, IsNotEmpty, IsNumber, IsOptional, IsString } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class CreateEventDto {
  @ApiProperty({ description: '적용할 방 ID', example: 1 })
  @IsNumber()
  @IsNotEmpty()
  roomId: number;

  @ApiProperty({ description: '조건 종류 (예: TEMP, HUMIDITY, FINE_DUST)', example: 'FINE_DUST' })
  @IsString()
  @IsNotEmpty()
  conditionType: string;

  @ApiProperty({ description: '조건 연산자 (예: GT, LT, EQ)', example: 'GT' })
  @IsString()
  @IsNotEmpty()
  conditionOperator: string;

  @ApiProperty({ description: '임계값 (조건 기준 수치)', example: 100 })
  @IsNumber()
  @IsNotEmpty()
  thresholdValue: number;

  @ApiProperty({ description: '실행할 모듈 타입 (예: AIR_PURIFIER)', example: 'AIR_PURIFIER' })
  @IsString()
  @IsNotEmpty()
  actionModuleType: string;

  @ApiProperty({ description: '모듈 전원 상태 제어 (true: 켜기, false: 끄기)', example: true, required: false })
  @IsBoolean()
  @IsOptional()
  actionModulePower?: boolean;

  @ApiProperty({ description: '모듈 작동 세기/레벨', example: 1, required: false })
  @IsNumber()
  @IsOptional()
  actionModuleLevel?: number;

  @ApiProperty({ description: '이벤트의 활성화 여부', example: true, required: false })
  @IsBoolean()
  @IsOptional()
  isActive?: boolean;
}
