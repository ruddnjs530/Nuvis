import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsString, IsNumber, IsOptional, IsBoolean, IsEnum } from 'class-validator';

export enum TaskType {
  MOVE_AND_EXECUTE = 0,
  MOVE_ONLY = 1,
  MODULE_ONLY = 2,
  RETURN_HOME = 3,
}

export class ExecuteCommandDto {
  @ApiPropertyOptional({ description: '명령어 고유 ID (없으면 자동 생성)' })
  @IsString()
  @IsOptional()
  commandId?: string;

  @ApiPropertyOptional({ description: '작업 고유 ID (없으면 자동 생성)' })
  @IsString()
  @IsOptional()
  taskId?: string;

  @ApiProperty({ description: '작업 유형 (0: 이동 후 실행, 1: 이동만, 2: 제자리 실행, 3: 복귀)', enum: TaskType, example: TaskType.MOVE_ONLY })
  @IsEnum(TaskType)
  taskType: TaskType;

  @ApiPropertyOptional({ description: '목표 구역 (예: entrance)', example: 'entrance' })
  @IsString()
  @IsOptional()
  targetZone?: string;

  @ApiPropertyOptional({ description: '목표 X 좌표', example: 0.0 })
  @IsNumber()
  @IsOptional()
  targetX?: number;

  @ApiPropertyOptional({ description: '목표 Y 좌표', example: 0.0 })
  @IsNumber()
  @IsOptional()
  targetY?: number;

  @ApiPropertyOptional({ description: '목표 회전각 (Yaw)', example: 0.0 })
  @IsNumber()
  @IsOptional()
  targetYaw?: number;

  @ApiPropertyOptional({ description: '작동할 모듈 타입 ID (1: 청정기 등)', example: 1 })
  @IsNumber()
  @IsOptional()
  moduleType?: number;

  @ApiPropertyOptional({ description: '모듈 전원 상태 제어', example: true })
  @IsBoolean()
  @IsOptional()
  modulePower?: boolean;

  @ApiPropertyOptional({ description: '모듈 세기 레벨', example: 1 })
  @IsNumber()
  @IsOptional()
  moduleLevel?: number;

  @ApiPropertyOptional({ description: '최대 실행 대기 시간 (초)', example: 180 })
  @IsNumber()
  @IsOptional()
  maxExecSec?: number;
}

export class ManualControlDto {
  @ApiProperty({ description: '선속도 (Linear Velocity X)', example: 0.5 })
  @IsNumber()
  vx: number;

  @ApiProperty({ description: '각속도 (Angular Velocity Z)', example: 0.0 })
  @IsNumber()
  wz: number;

  @ApiPropertyOptional({ description: '해당 명령을 지속할 시간 (ms)', example: 1000 })
  @IsNumber()
  @IsOptional()
  durationMs?: number;
}
