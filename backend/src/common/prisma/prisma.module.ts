<<<<<<< HEAD
import { Module } from '@nestjs/common';
import { PrismaService } from './prisma.service';

=======
import { Global, Module } from '@nestjs/common';
import { PrismaService } from './prisma.service';

@Global()
>>>>>>> origin/infra/task/ci-cd-setup
@Module({
  providers: [PrismaService],
  exports: [PrismaService],
})
export class PrismaModule {}
