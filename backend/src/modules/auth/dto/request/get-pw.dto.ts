import { ApiProperty } from '@nestjs/swagger';
import { IsEmail, IsString, Matches } from 'class-validator';

export class GetPwDto {
  @IsString()
  @ApiProperty({
    description: '계정 비밀번호',
  })
  pw: string;
}
