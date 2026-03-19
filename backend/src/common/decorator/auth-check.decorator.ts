import {
  BadRequestException,
  ForbiddenException,
  UnauthorizedException,
  UseGuards,
  applyDecorators,
} from '@nestjs/common';
import { Rank } from './rank.decorator';
import { RankGuard } from '../guard/auth.guard';
import { ApiBearerAuth, ApiResponse } from '@nestjs/swagger';
import { ApiException } from './api-exception.decorator';

export const AuthCheck = (rank: number) => {
  const decorators = [Rank(rank), UseGuards(RankGuard)];
  if (rank !== 0) {
    decorators.push(ApiBearerAuth());
    decorators.push(ApiException(new UnauthorizedException('token expired')));
    decorators.push(ApiException(new UnauthorizedException('Invalid token')));
    decorators.push(ApiException(new ForbiddenException('No permission')));
  }
  return applyDecorators(...decorators);
};
