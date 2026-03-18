import { IsNumber } from 'class-validator';

export class RegisterRobotDto {
  @IsNumber()
  userId: number;
}
