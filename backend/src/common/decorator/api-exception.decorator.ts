import { HttpException, applyDecorators } from '@nestjs/common';
import { ApiResponse } from '@nestjs/swagger';

export const ApiException = (exception: HttpException) => {
  return ApiResponse({
    status: exception.getStatus(),
    description: exception.message,
  });
};
