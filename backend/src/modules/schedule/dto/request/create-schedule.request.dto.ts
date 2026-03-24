import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsString, IsNumber, IsBoolean, IsOptional, IsDateString } from 'class-validator';

export class CreateScheduleDto {
  @ApiProperty({ description: '방 ID', example: 1 })
  @IsNumber()
  roomId: number;

  @ApiProperty({ description: '가동할 모듈 종류', example: 'AIR_PURIFIER' })
  @IsString()
  actionModuleType: string;

  @ApiPropertyOptional({ description: '모듈 전원 상태 제어', example: true, default: true })
  @IsBoolean()
  @IsOptional()
  actionModulePower?: boolean;

  @ApiPropertyOptional({ description: '모듈 세기 레벨', example: 2, default: 1 })
  @IsNumber()
  @IsOptional()
  actionModuleLevel?: number;

  @ApiProperty({ description: '스케줄 매일 가동 시간 (ISO 8601형식 시간부 사용, 날짜 무시)', example: '1970-01-01T14:30:00.000Z' })
  @IsDateString()
  startTime: string;

  @ApiProperty({ description: '스케줄 총 지속 시간(분)', example: 60 })
  @IsNumber()
  durationMinutes: number;

  @ApiProperty({ description: '스케줄 활성화 여부', example: true })
  @IsBoolean()
  isActive: boolean;
}
