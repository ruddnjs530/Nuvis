import { Test, TestingModule } from '@nestjs/testing';
import { RobotController } from './robot.controller';
import { RobotService } from '../services/robot.service';
import { ExecuteCommandDto, TaskType } from '../dto/request/execute-command.request.dto';
import { ManualControlDto } from '../dto/request/manual-control.request.dto';
import { User } from 'src/modules/auth/models/user.model';
import { RankGuard } from 'src/common/guard/auth.guard';

describe('RobotController', () => {
  let controller: RobotController;
  let service: RobotService;

  const mockRobotService = {
    getAiDataset: jest.fn(),
    executeTask: jest.fn(),
    manualControl: jest.fn(),
    getStatus: jest.fn(),
  };

  const mockUser: User = { userId: 1, email: 'test@test.com', name: 'tester' };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [RobotController],
      providers: [
        { provide: RobotService, useValue: mockRobotService },
      ],
    })
    .overrideGuard(RankGuard)
    .useValue({ canActivate: jest.fn().mockReturnValue(true) })
    .compile();

    controller = module.get<RobotController>(RobotController);
    service = module.get<RobotService>(RobotService);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  describe('executeCommand', () => {
    it('should call executeTask and return its result', async () => {
      const dto: ExecuteCommandDto = { taskType: TaskType.MOVE_AND_EXECUTE, moduleType: 1 };
      const expectedResult = { accepted: true };
      (service.executeTask as jest.Mock).mockResolvedValue(expectedResult);

      const result = await controller.executeCommand(dto);
      expect(service.executeTask).toHaveBeenCalledWith(dto);
      expect(result).toEqual(expectedResult);
    });
  });

  describe('manualControl', () => {
    it('should call manualControl and return result', async () => {
      const dto: ManualControlDto = { vx: 0.1, wz: 0 };
      const expectedResult = { accepted: true };
      (service.manualControl as jest.Mock).mockResolvedValue(expectedResult);

      const result = await controller.manualControl(dto);
      expect(service.manualControl).toHaveBeenCalledWith(dto);
      expect(result).toEqual(expectedResult);
    });
  });

  describe('getStatus', () => {
    it('should call getStatus and wrap it in data object', async () => {
      const expectedStatus = { robot_id: 'R1', battery_pct: 100 };
      (service.getStatus as jest.Mock).mockResolvedValue(expectedStatus);

      const result = await controller.getStatus();
      expect(service.getStatus).toHaveBeenCalled();
      expect(result).toEqual({ data: expectedStatus });
    });
  });
});
