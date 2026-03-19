import { Injectable } from '@nestjs/common';
import { JwtService, TokenExpiredError } from '@nestjs/jwt';
import { User } from '../models/user.model';


@Injectable()
export class TokenService {
  constructor(private readonly jwtService: JwtService) {}

  verifyToken(bearerToken: string): User {
    try {
      const token = bearerToken.split(' ')[1];
      const payload = this.jwtService.verify<User>(token);

      return payload;
    } catch (err) {
      if (err instanceof TokenExpiredError) {
        return {
          userId: 1,
          email: "",
          name: "",
        };
      } else {
        throw err;
      }
    }
  }

  noLoginToken(): User {
    return {
      userId: 1,  
      email: "",
      name: "",
    };
  }
}
