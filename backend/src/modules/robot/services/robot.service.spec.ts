import { Test, TestingModule } from '@nestjs/testing';
import { RobotService } from './robot.service';
import { RobotRepository } from '../repositories/robot.repository';
import { of, throwError } from 'rxjs';
import { ExecuteCommandDto, TaskType } from '../dto/request/execute-command.request.dto';
import { ManualControlDto } from '../dto/request/manual-control.request.dto';
import { ClientGrpc } from '@nestjs/microservices';

describe('RobotService', () => {
  let service: RobotService;

  const mockRobotGateway = {
    executeTask: jest.fn(),
    manualControl: jest.fn(),
    getStatus: jest.fn(),
  };

  const mockClientGrpc = {
    getService: jest.fn().mockReturnValue(mockRobotGateway),
  };

  const mockRobotRepository = {};

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        RobotService,
        { provide: RobotRepository, useValue: mockRobotRepository },
        { provide: 'ROBOT_GRPC_CLIENT', useValue: mockClientGrpc },
      ],
    }).compile();

    service = module.get<RobotService>(RobotService);
    // Initialize the module to bind the gateway
    service.onModuleInit();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('executeTask', () => {
    it('should successfully call grpc executeTask', async () => {
      const dto: ExecuteCommandDto = {
        commandId: 'test-1',
        taskId: 't-1',
        taskType: TaskType.MOVE_AND_EXECUTE,
        targetZone: 'hq',
        moduleType: 1,
      };

      const expectedResponse = { accepted: true, message: 'Success' };
      mockRobotGateway.executeTask.mockReturnValue(of(expectedResponse));

      const result = await service.executeTask(dto);
      
      expect(result).toEqual(expectedResponse);
      expect(mockRobotGateway.executeTask).toHaveBeenCalledWith(expect.objectContaining({
        targetZone: 'hq',
        targetX: 0, // Should be 0 when zone is defined
        targetY: 0,
      }));
    });

    it('should throw error when grpc fails', async () => {
      mockRobotGateway.executeTask.mockReturnValue(throwError(() => new Error('gRPC Error')));
      
      const dto = new ExecuteCommandDto();
      await expect(service.executeTask(dto)).rejects.toThrow('gRPC Error');
    });
  });

  describe('manualControl', () => {
    it('should send manual control command successfully', async () => {
      const dto: ManualControlDto = { vx: 1.0, wz: 0.5, durationMs: 2000 };
      const expectedResponse = { accepted: true };
      
      mockRobotGateway.manualControl.mockReturnValue(of(expectedResponse));

      const result = await service.manualControl(dto);
      
      expect(result).toEqual(expectedResponse);
      expect(mockRobotGateway.manualControl).toHaveBeenCalledWith({
        vx: 1.0, wz: 0.5, durationMs: 2000
      });
    });
  });

  describe('getStatus', () => {
    it('should fallback to mock status if grpc call fails', async () => {
      mockRobotGateway.getStatus.mockReturnValue(throwError(() => new Error('Network Error')));

      const result = await service.getStatus();
      expect(result).toBeDefined();
      expect(result.attached_module.name).toBe('AIR_PURIFIER');
      expect(result.robot_id).toBe('robot-R1'); // mock value
    });

    it('should return successfully wrapped status from grpc', async () => {
      const liveStatus = {
        robot_id: 'real-robot',
        pose_x: 5.5,
      };
      mockRobotGateway.getStatus.mockReturnValue(of(liveStatus));

      const result = await service.getStatus();
      expect(result.robot_id).toBe('real-robot');
      expect(result.attached_module.name).toBe('AIR_PURIFIER');
    });
  });
});
