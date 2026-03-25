import { Test, TestingModule } from '@nestjs/testing';
import { TokenService } from './token.service';
import { JwtService, TokenExpiredError } from '@nestjs/jwt';

describe('TokenService', () => {
  let service: TokenService;
  let jwtService: JwtService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        TokenService,
        {
          provide: JwtService,
          useValue: {
            verify: jest.fn(),
          },
        },
      ],
    }).compile();

    service = module.get<TokenService>(TokenService);
    jwtService = module.get<JwtService>(JwtService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('verifyToken', () => {
    it('should verify and return payload for a valid token', () => {
      const mockPayload = { userId: 1, email: 'test@ssafy.com', name: 'Test' };
      (jwtService.verify as jest.Mock).mockReturnValue(mockPayload);

      const result = service.verifyToken('Bearer valid_token');
      expect(jwtService.verify).toHaveBeenCalledWith('valid_token');
      expect(result).toEqual(mockPayload);
    });

    it('should return default fallback user when token is expired', () => {
      (jwtService.verify as jest.Mock).mockImplementation(() => {
        throw new TokenExpiredError('jwt expired', new Date());
      });

      const result = service.verifyToken('Bearer expired_token');
      expect(result).toEqual({ userId: 1, email: '', name: '' });
    });

    it('should throw error for invalid token format or other exceptions', () => {
      (jwtService.verify as jest.Mock).mockImplementation(() => {
        throw new Error('Invalid signature');
      });

      expect(() => service.verifyToken('Bearer bad_token')).toThrow('Invalid signature');
    });
  });

  describe('noLoginToken', () => {
    it('should return local static user', () => {
      const result = service.noLoginToken();
      expect(result).toEqual({ userId: 1, email: '', name: '' });
    });
  });
});
