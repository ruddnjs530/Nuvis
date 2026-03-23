import {
  Body,
  Controller,
  Delete,
  Get,
  Patch,
  Post,
  Put,
  UnauthorizedException,
} from '@nestjs/common';
import { AuthService } from '../services/auth.service';
import { SignInDto } from '../dto/request/sign-in.dto';
import { ApiTags } from '@nestjs/swagger';
import { TokenResponseDto } from '../dto/response/token.dto';
import { ExceptionList } from 'src/common/decorator/exception-list.decorator';

@ApiTags('Auth API')
@Controller('api/auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  /**
   * 로그인
   */
  @Post('/login')
  @ExceptionList([])
  async signIn(@Body() signInDto: SignInDto): Promise<TokenResponseDto> {
    const accessToken = await this.authService.signIn(signInDto);

    return {
      accessToken: accessToken,
    };
  }

}
