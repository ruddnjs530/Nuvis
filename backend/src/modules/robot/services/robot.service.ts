import { Injectable } from '@nestjs/common';
import { RobotRepository } from '../repositories/robot.repository';

@Injectable()
export class RobotService {
  constructor(private readonly robotRepository: RobotRepository) {}

  create(data: any) {
    // TODO: Implement robot creation logic
    return { ...data, createdAt: new Date() };
  }
}
