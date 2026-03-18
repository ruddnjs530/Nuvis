import { Injectable, OnModuleDestroy, OnModuleInit } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { PrismaClient } from '../../../generated/prisma/client';
import { PrismaMariaDb } from '@prisma/adapter-mariadb';

@Injectable()
export class PrismaService
  extends PrismaClient
  implements OnModuleInit, OnModuleDestroy
{
  constructor(private configService: ConfigService) {
    const databaseUrl = configService.get<string>('DATABASE_URL');
    let poolOptions: any;

    if (databaseUrl) {
      const url = new URL(databaseUrl);
      poolOptions = {
        host: url.hostname,
        port: Number(url.port) || 3306,
        user: url.username, // Using user parameter for MariaDB adapter
        password: url.password,
        database: url.pathname.slice(1),
        connectionLimit: 10,
        connectTimeout: 5000,
        idleTimeout: 300,
      };
    } else {
      poolOptions = {
        host: configService.get<string>('DB_HOST') || 'localhost',
        port: Number(configService.get<string>('DB_PORT') || 3306),
        user: configService.get<string>('DB_USER') || 'root',
        password: configService.get<string>('DB_PASSWORD') || '1234',
        database: configService.get<string>('DB_NAME') || 'app_db',
        connectionLimit: 10,
        connectTimeout: 5000,
        idleTimeout: 300,
      };
    }

    const adapter = new PrismaMariaDb(poolOptions);

    super({ adapter });
  }

  async onModuleInit() {
    try {
      await this.$connect();
    } catch (error) {
      console.error('Failed to connect to the database:', error);
    }
  }

  async onModuleDestroy() {
    try {
      await this.$disconnect();
    } catch (error) {
      console.error('Failed to disconnect from the database:', error);
    }
  }
}
