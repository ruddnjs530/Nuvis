import { Injectable } from '@nestjs/common';

import { PrismaService } from 'src/common/prisma/prisma.service';

@Injectable()
export class AuthRepository {
constructor(private readonly prismaService: PrismaService) {}

    async selectAccountById(id: number) {
        return this.prismaService.user.findFirst({
            where: { userId: id,},
        });
    }

    async selectAccountByEmail(email: string) {
        return this.prismaService.user.findFirst({
            where: { email: email },
        });
    }
}
