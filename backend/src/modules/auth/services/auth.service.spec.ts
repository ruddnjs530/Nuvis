import { Test, TestingModule } from '@nestjs/testing';
import { AuthService } from './auth.service';
import { JwtService } from '@nestjs/jwt';
import { PrismaService } from 'src/common/prisma/prisma.service';
import { AuthRepository } from '../repositories/auth.repository';
import { LoginFailException } from '../exception/LoginFail.exception';
import * as bcrypt from 'bcrypt';

describe('AuthService', () => {
  let service: AuthService;
  let authRepository: AuthRepository;
  let jwtService: JwtService;

  const mockJwtService = {
    signAsync: jest.fn(),
  };

  const mockPrismaService = {};

  const mockAuthRepository = {
    selectAccountByEmail: jest.fn(),
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        AuthService,
        { provide: JwtService, useValue: mockJwtService },
        { provide: PrismaService, useValue: mockPrismaService },
        { provide: AuthRepository, useValue: mockAuthRepository },
      ],
    }).compile();

    service = module.get<AuthService>(AuthService);
    authRepository = module.get<AuthRepository>(AuthRepository);
    jwtService = module.get<JwtService>(JwtService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('signIn', () => {
    it('should successfully login and return a JWT token', async () => {
      // Mock db user
      const plainPw = '1234';
      const passwordHash = bcrypt.hashSync(plainPw, 10);
      const mockUser = {
        userId: 1,
        email: 'user@ssafy.com',
        name: 'User',
        passwordHash,
      };

      (authRepository.selectAccountByEmail as jest.Mock).mockResolvedValue(mockUser);
      (jwtService.signAsync as jest.Mock).mockResolvedValue('mocked_jwt_token');

      const result = await service.signIn({ email: 'user@ssafy.com', pw: plainPw });
      expect(result).toBe('mocked_jwt_token');
      expect(jwtService.signAsync).toHaveBeenCalledWith({
        userId: mockUser.userId,
        email: mockUser.email,
        name: mockUser.name,
      });
    });

    it('should throw LoginFailException when user is not found', async () => {
      (authRepository.selectAccountByEmail as jest.Mock).mockResolvedValue(null);

      await expect(service.signIn({ email: 'unknown@ssafy.com', pw: '1234' }))
        .rejects.toThrow(LoginFailException);
    });

    it('should throw LoginFailException when password does not match', async () => {
      const passwordHash = bcrypt.hashSync('correct', 10);
      const mockUser = {
        userId: 1,
        email: 'user@ssafy.com',
        name: 'User',
        passwordHash,
      };

      (authRepository.selectAccountByEmail as jest.Mock).mockResolvedValue(mockUser);

      await expect(service.signIn({ email: 'user@ssafy.com', pw: 'wrong_password' }))
        .rejects.toThrow(LoginFailException);
    });
  });
});
