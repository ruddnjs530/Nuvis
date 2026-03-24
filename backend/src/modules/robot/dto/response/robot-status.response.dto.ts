import { ApiProperty } from '@nestjs/swagger';

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
