import { IsBoolean, IsNumber, IsOptional, IsString } from 'class-validator';
import { ApiPropertyOptional } from '@nestjs/swagger';

export class UpdateEventDto {
  @ApiPropertyOptional({ description: '조건 종류 (예: TEMP, HUMIDITY, FINE_DUST)', example: 'FINE_DUST' })
  @IsString()
  @IsOptional()
  conditionType?: string;

  @ApiPropertyOptional({ description: '조건 연산자 (예: GT, LT, EQ)', example: 'GT' })
  @IsString()
  @IsOptional()
  conditionOperator?: string;

  @ApiPropertyOptional({ description: '임계값 (조건 기준 수치)', example: 120 })
  @IsNumber()
  @IsOptional()
  thresholdValue?: number;

  @ApiPropertyOptional({ description: '실행할 모듈 타입 (예: AIR_PURIFIER)', example: 'AIR_PURIFIER' })
  @IsString()
  @IsOptional()
  actionModuleType?: string;

  @ApiPropertyOptional({ description: '모듈 전원 상태 제어 (true: 켜기, false: 끄기)', example: true })
  @IsBoolean()
  @IsOptional()
  actionModulePower?: boolean;

  @ApiPropertyOptional({ description: '모듈 작동 세기/레벨', example: 2 })
  @IsNumber()
  @IsOptional()
  actionModuleLevel?: number;

  @ApiPropertyOptional({ description: '이벤트의 활성화 여부', example: false })
  @IsBoolean()
  @IsOptional()
  isActive?: boolean;
}
