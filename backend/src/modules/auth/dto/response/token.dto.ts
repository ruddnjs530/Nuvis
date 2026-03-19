import { ApiProperty } from '@nestjs/swagger';

export class TokenResponseDto {
  @ApiProperty({
    description: '토큰',
    default: 'token',
  })
  accessToken: string;
}
