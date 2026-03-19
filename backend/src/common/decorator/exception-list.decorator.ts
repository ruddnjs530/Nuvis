import { HttpException, applyDecorators } from '@nestjs/common';
import { ApiException } from './api-exception.decorator';

export const ExceptionList = (exceptionList: HttpException[]) => {
  return applyDecorators(...exceptionList.map((exception) => ApiException(exception)));
};
