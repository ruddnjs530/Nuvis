import { IsEmail, IsString, MinLength, IsNotEmpty } from 'class-validator';

export class CreateUserDto {
  @IsEmail({}, { message: 'Invalid email format' })
  email: string;

  @IsString()
  @IsNotEmpty({ message: 'Name cannot be empty' })
  name: string;

  @IsString()
  @MinLength(8, { message: 'Password hash must be at least 8 characters long' })
  passwordHash: string;
}
