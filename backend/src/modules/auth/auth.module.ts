import { Global, Module } from '@nestjs/common';
import { AuthController } from './controllers/auth.controller';
import { JwtModule } from '@nestjs/jwt';
import { AuthService } from './services/auth.service';
import { PrismaModule } from 'src/common/prisma/prisma.module';

import jwtConfig from './config/jwt.config';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { TokenService } from './services/token.service';
import { AuthRepository } from './repositories/auth.repository';

@Global()
@Module({
  imports: [
    JwtModule.registerAsync({
      imports: [ConfigModule.forFeature(jwtConfig)],
      useFactory: (configService: ConfigService) => configService.get('jwt')!,
      inject: [ConfigService],
    }),
    PrismaModule,
  ],
  providers: [AuthService, TokenService, AuthRepository],
  controllers: [AuthController],
  exports: [TokenService],
})
export class AuthModule {}
