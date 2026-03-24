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

export class AttachedModuleDto {
  @ApiProperty({ description: '장착된 모듈 타입 (예: 1 - AIR_PURIFIER)', example: 1 })
  type: number;

  @ApiProperty({ description: '모듈 이름', example: 'AIR_PURIFIER' })
  name: string;

  @ApiProperty({ description: '모듈 사용 가능 여부', example: true })
  is_available: boolean;
}

export class ResponseRobotStatusDto {
  @ApiProperty({ description: '로봇 고유 ID', example: 'robot-R1' })
  robot_id: string;

  @ApiProperty({ description: '로봇 구동 모드', example: 0 })
  mode: number;

  @ApiProperty({ description: '로봇 작업 상태', example: 0 })
  task_state: number;

  @ApiProperty({ description: '현재 수행중인 작업 ID', example: 'task-1710000000' })
  active_task_id: string;

  @ApiProperty({ description: '배터리 잔량 (%)', example: 85.5 })
  battery_pct: number;

  @ApiProperty({ description: '충전 중 여부', example: false })
  is_charging: boolean;

  @ApiProperty({ description: '로봇 안전 상태', example: 0 })
  safety_state: number;

  @ApiProperty({ description: '최근 오류 코드', example: 0 })
  last_error_code: number;

  @ApiProperty({ description: 'X 좌표', example: 10.5 })
  pose_x: number;

  @ApiProperty({ description: 'Y 좌표', example: 20.3 })
  pose_y: number;

  @ApiProperty({ description: '로봇 회전각 (Yaw)', example: 1.57 })
  pose_yaw: number;

  @ApiProperty({ description: '상태 갱신 시각 (ISO)', example: '2026-03-24T17:00:00.000Z' })
  stamp: string;

  @ApiProperty({ description: '현재 장착된 시스템 모듈 상태', type: AttachedModuleDto })
  attached_module: AttachedModuleDto;
}
