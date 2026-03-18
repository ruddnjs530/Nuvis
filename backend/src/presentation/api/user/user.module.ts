import { Module } from '@nestjs/common';
import { UserController } from './user.controller';
import { CreateUserUseCase } from '../../../application/user/usecases/create-user.usecase';
import { PrismaModule } from '../../../infrastructure/database/prisma/prisma.module';

@Module({
  imports: [PrismaModule],
  controllers: [UserController],
  providers: [CreateUserUseCase],
  exports: [CreateUserUseCase],
})
export class UserApiModule {}
