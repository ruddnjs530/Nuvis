import { IsNumber, IsString, IsNotEmpty } from 'class-validator';

export class CreateEventDto {
  @IsNumber()
  userId: number;

  @IsNumber()
  roomId: number;

  @IsString()
  @IsNotEmpty({ message: 'Condition type is required' })
  conditionType: string;

  @IsString()
  @IsNotEmpty({ message: 'Condition operator is required' })
  conditionOperator: string;

  @IsNumber()
  thresholdValue: number;

  @IsString()
  @IsNotEmpty({ message: 'Action module type is required' })
  actionModuleType: string;
}
