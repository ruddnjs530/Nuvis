import { IsNumber, IsString, IsNotEmpty, IsOptional } from 'class-validator';

export class CreateRoomDto {
  @IsNumber()
  userId: number;

  @IsString()
  @IsNotEmpty({ message: 'Room name cannot be empty' })
  name: string;

  @IsOptional()
  mapData?: any;
}
