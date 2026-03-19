import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
  Logger,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  private readonly logger = new Logger('HTTP');

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const { method, originalUrl, body, query } = request;
    const ip = request.ip;

    const bodyStr = Object.keys(body || {}).length ? JSON.stringify(body) : '';
    const queryStr = Object.keys(query || {}).length ? JSON.stringify(query) : '';
    
    this.logger.log(
      `[REQ] ${method} ${originalUrl} - IP: ${ip} - Query: ${queryStr} - Body: ${bodyStr}`,
    );

    const now = Date.now();
    return next.handle().pipe(
      tap(() => {
        const response = context.switchToHttp().getResponse();
        const statusCode = response.statusCode;
        this.logger.log(
          `[RES] ${method} ${originalUrl} ${statusCode} - ${Date.now() - now}ms`,
        );
      }),
    );
  }
}
