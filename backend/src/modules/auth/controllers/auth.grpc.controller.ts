import { Controller } from '@nestjs/common';
import { GrpcMethod } from '@nestjs/microservices';
import { AuthService } from '../services/auth.service';

@Controller()
export class AuthGrpcController {
  constructor(private readonly service: AuthService) {}

  @GrpcMethod('AuthService', 'CreateAuth')
  create(data: any) {
    return this.service.create(data);
  }
}
