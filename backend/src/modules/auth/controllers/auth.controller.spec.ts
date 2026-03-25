import { Test, TestingModule } from '@nestjs/testing';
import { AuthController } from './auth.controller';
import { AuthService } from '../services/auth.service';

describe('AuthController', () => {
  let controller: AuthController;
  let authService: AuthService;

  const mockAuthService = {
    signIn: jest.fn(),
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [AuthController],
      providers: [
        {
          provide: AuthService,
          useValue: mockAuthService,
        },
      ],
    }).compile();

    controller = module.get<AuthController>(AuthController);
    authService = module.get<AuthService>(AuthService);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  describe('signIn', () => {
    it('should return token object on successful login', async () => {
      const token = 'generated_token_string';
      (authService.signIn as jest.Mock).mockResolvedValue(token);

      const dto = { email: 'test@ssafy.com', pw: '1234' };
      const result = await controller.signIn(dto);
      
      expect(authService.signIn).toHaveBeenCalledWith(dto);
      expect(result).toEqual({ accessToken: token });
    });
  });
});
