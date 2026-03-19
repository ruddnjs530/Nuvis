import { HttpException } from '@nestjs/common';
import { ErrorCodes } from 'src/common/lib/error-code';

export class LoginFailException extends HttpException {
  constructor() {
    super('login fail', ErrorCodes.LOGIN_FAIL);
  }
}
