import { Test, TestingModule } from '@nestjs/testing';
import { ScheduleController } from './schedule.controller';
import { ScheduleService } from '../services/schedule.service';
import { User } from 'src/modules/auth/models/user.model';
import { CreateScheduleDto } from '../dto/request/create-schedule.request.dto';
import { UpdateScheduleDto } from '../dto/request/update-schedule.request.dto';
import { RankGuard } from 'src/common/guard/auth.guard';

describe('ScheduleController', () => {
  let controller: ScheduleController;
  let service: ScheduleService;

  const mockScheduleService = {
    findAllByUserId: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
  };

  const mockUser: User = { userId: 1, email: 'usr@test.com', name: 'user' };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [ScheduleController],
      providers: [
        { provide: ScheduleService, useValue: mockScheduleService },
      ],
    })
    .overrideGuard(RankGuard)
    .useValue({ canActivate: jest.fn().mockReturnValue(true) })
    .compile();

    controller = module.get<ScheduleController>(ScheduleController);
    service = module.get<ScheduleService>(ScheduleService);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  describe('getSchedules', () => {
    it('should return array wrapped in data', async () => {
      const expected = [{ scheduleId: 1 }];
      (service.findAllByUserId as jest.Mock).mockResolvedValue(expected);

      const result = await controller.getSchedules(mockUser);
      expect(service.findAllByUserId).toHaveBeenCalledWith(mockUser.userId);
      expect(result).toEqual({ data: expected });
    });
  });

  describe('createSchedule', () => {
    it('should return created schedule wrapped in data', async () => {
      const dto = new CreateScheduleDto();
      const expected = { scheduleId: 2 };
      (service.create as jest.Mock).mockResolvedValue(expected);

      const result = await controller.createSchedule(mockUser, dto);
      expect(service.create).toHaveBeenCalledWith(mockUser.userId, dto);
      expect(result).toEqual({ data: expected });
    });
  });

  describe('updateSchedule', () => {
    it('should return updated schedule wrapped in data', async () => {
      const dto = new UpdateScheduleDto();
      const expected = { scheduleId: 1 };
      (service.update as jest.Mock).mockResolvedValue(expected);

      const result = await controller.updateSchedule('1', dto);
      expect(service.update).toHaveBeenCalledWith(1, dto);
      expect(result).toEqual({ data: expected });
    });
  });

  describe('deleteSchedule', () => {
    it('should execute delete service successfully', async () => {
      const result = await controller.deleteSchedule('1');
      expect(service.delete).toHaveBeenCalledWith(1);
      expect(result).toEqual({ message: 'Schedule deleted successfully' });
    });
  });
});
