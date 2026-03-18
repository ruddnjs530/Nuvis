import { IsDateString, IsNumber, IsString, IsNotEmpty, Min } from 'class-validator';

export class CreateScheduleDto {
  @IsNumber()
  userId: number;

  @IsNumber()
  roomId: number;

  @IsString()
  @IsNotEmpty({ message: 'Action module type is required' })
  actionModuleType: string;

  @IsDateString({}, { message: 'Must be a valid ISO Date/Time string' })
  startTime: string;

  @IsNumber()
  @Min(1)
  durationMinutes: number;
}
