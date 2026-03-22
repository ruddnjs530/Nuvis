import { Injectable, UnauthorizedException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { PrismaService } from 'src/common/prisma/prisma.service';
import { SignInDto } from '../dto/request/sign-in.dto';
import { compareSync, hashSync } from 'bcrypt';
import { AuthRepository } from '../repositories/auth.repository';
import { LoginFailException } from '../exception/LoginFail.exception';
@Injectable()
export class AuthService {
  constructor(
    private readonly jwtService: JwtService,
    private readonly prisma: PrismaService,
    private readonly authRepository: AuthRepository,
  ) {}

  async signIn(signInDto: SignInDto): Promise<string> {
    const user = await this.authRepository.selectAccountByEmail(signInDto.email);

    if (!user || !user.passwordHash) {
      throw new LoginFailException();
    }
    const passwordMatch = compareSync(signInDto.pw, user.passwordHash);

    if (!passwordMatch) {
      throw new LoginFailException();
    }

    return await this.jwtService.signAsync({
      userId: user.userId,
      email: user.email,
      name: user.name,
    });
  }




  create(data: any) {
    // Skeleton method added to pass compilation
    return { ...data, createdAt: new Date() };
  }
}
