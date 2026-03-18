import { Controller, Post, Body, HttpCode, HttpStatus } from '@nestjs/common';
import { CreateUserUseCase } from '../../../application/user/usecases/create-user.usecase';
import { CreateUserDto } from './dto/create-user.dto';

@Controller('users')
export class UserController {
  constructor(private readonly createUserUseCase: CreateUserUseCase) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  async createUser(@Body() createUserDto: CreateUserDto) {
    const user = await this.createUserUseCase.execute({
      email: createUserDto.email,
      name: createUserDto.name,
      passwordHash: createUserDto.passwordHash,
    });

    return {
      message: 'User created successfully',
      data: {
        id: user.id,
        email: user.email.value,
        name: user.name,
        createdAt: user.createdAt,
      },
    };
  }
}
