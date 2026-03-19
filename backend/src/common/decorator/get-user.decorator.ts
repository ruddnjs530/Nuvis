import { ExecutionContext, createParamDecorator } from '@nestjs/common';
import { User } from 'src/modules/auth/models/user.model';

export const GetUser = createParamDecorator(
  (data, ctx: ExecutionContext): User => {
    const req = ctx.switchToHttp().getRequest();
    return req.user;
  },
);
