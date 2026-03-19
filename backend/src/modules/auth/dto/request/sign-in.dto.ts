import { ApiProperty } from '@nestjs/swagger';
import { Type } from 'class-transformer';
import { IsEmail, IsOptional, IsString } from 'class-validator';

export class SignInDto {
  @IsString()
  @ApiProperty({
    description: '로그인 이메일',
    default: 'juneh2633@gmail.com',
  })
  email: string;

  @IsString()
  @ApiProperty({
    description: '로그인 비밀번호',
  })
  pw: string;
}
