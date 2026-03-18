import { Injectable } from '@nestjs/common';
import { User, UserProps } from '../../../domain/user/user.entity';
import { EmailVO } from '../../../domain/user/vo/email.vo';
import { PasswordHashVO } from '../../../domain/user/vo/password-hash.vo';
import { PrismaService } from '../../../infrastructure/database/prisma/prisma.service';

export interface CreateUserCommand {
  email: string;
  name: string;
  passwordHash: string; // Plain password hashing left for future Auth Module
}

@Injectable()
export class CreateUserUseCase {
  constructor(private readonly prisma: PrismaService) {}

  async execute(command: CreateUserCommand): Promise<User> {
    // 1. Create Domain Value Objects
    const email = EmailVO.create(command.email);
    const passwordHash = PasswordHashVO.create(command.passwordHash);

    // 2. Map valid VO's to Entity payload
    const userProps: UserProps = {
      email,
      name: command.name,
      passwordHash,
    };
    
    // (Optional) Domain Entity checks before saving
    const user = User.create(null, userProps);

    // 3. Save via Infrastructure
    const savedRecord = await this.prisma.user.create({
      data: {
        email: user.email.value,
        name: user.name,
        passwordHash: user.passwordHash.value,
      },
    });

    // 4. Return reconstructed entity with DB ID
    return User.create(savedRecord.userId, {
      email: EmailVO.create(savedRecord.email),
      name: savedRecord.name,
      passwordHash: PasswordHashVO.create(savedRecord.passwordHash),
      createdAt: savedRecord.createdAt,
    });
  }
}
