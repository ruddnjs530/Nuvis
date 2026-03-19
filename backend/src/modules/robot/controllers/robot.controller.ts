import { Controller } from '@nestjs/common';
import { RobotService } from '../services/robot.service';

@Controller('robot')
export class RobotController {
  constructor(private readonly robotService: RobotService) {}
}
