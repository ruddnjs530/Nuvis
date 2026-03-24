import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsNumber, IsOptional } from 'class-validator';

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
