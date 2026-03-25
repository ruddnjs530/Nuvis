import { Test, TestingModule } from '@nestjs/testing';
import { ScheduleService } from './schedule.service';
import { ScheduleRepository } from '../repositories/schedule.repository';
import { RobotService } from '../../robot/services/robot.service';
import { SchedulerRegistry } from '@nestjs/schedule';

// Mock cron to prevent actual timers from leaking in testing
jest.mock('cron', () => {
  return {
    CronJob: jest.fn().mockImplementation(() => {
      return { stop: jest.fn(), start: jest.fn() };
    }),
  };
});

describe('ScheduleService', () => {
  let service: ScheduleService;

  const mockScheduleRepository = {
    findAllByUserId: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
  };

  const mockRobotService = {
    executeTask: jest.fn(),
    getAiDataset: jest.fn(),
  };

  const mockSchedulerRegistry = {
    getCronJobs: jest.fn().mockReturnValue(new Map()),
    deleteCronJob: jest.fn(),
    addCronJob: jest.fn(),
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        ScheduleService,
        { provide: ScheduleRepository, useValue: mockScheduleRepository },
        { provide: RobotService, useValue: mockRobotService },
        { provide: SchedulerRegistry, useValue: mockSchedulerRegistry },
      ],
    }).compile();

    service = module.get<ScheduleService>(ScheduleService);
    
    // reset global fetch
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('findAllByUserId', () => {
    it('should return all schedules for a user', async () => {
      const expected = [{ scheduleId: 1 }];
      mockScheduleRepository.findAllByUserId.mockResolvedValue(expected);

      const result = await service.findAllByUserId(1);
      expect(mockScheduleRepository.findAllByUserId).toHaveBeenCalledWith(1);
      expect(result).toEqual(expected);
    });
  });

  describe('create & registerJob', () => {
    it('should create schedule and register dynamic cron job if active', async () => {
      const mockDto = { isActive: true, startTime: new Date().toISOString() };
      const expected = { scheduleId: 1, ...mockDto };
      mockScheduleRepository.create.mockResolvedValue(expected);

      mockSchedulerRegistry.getCronJobs.mockReturnValue(new Map());

      const result = await service.create(1, mockDto as any);
      expect(mockScheduleRepository.create).toHaveBeenCalledWith(1, mockDto);
      expect(mockSchedulerRegistry.addCronJob).toHaveBeenCalledWith('schedule-1', expect.anything());
      expect(result).toEqual(expected);
    });
  });

  describe('update & delete job', () => {
    it('should update schedule and re-register job', async () => {
      const mockDto = { isActive: false };
      const expected = { scheduleId: 1, ...mockDto };
      mockScheduleRepository.update.mockResolvedValue(expected);

      const jobMap = new Map();
      jobMap.set('schedule-1', {});
      mockSchedulerRegistry.getCronJobs.mockReturnValue(jobMap);

      const result = await service.update(1, mockDto as any);
      
      expect(mockSchedulerRegistry.deleteCronJob).toHaveBeenCalledWith('schedule-1');
      // Because isActive is false, addCronJob should not be called
      expect(mockSchedulerRegistry.addCronJob).not.toHaveBeenCalled();
      expect(result).toEqual(expected);
    });
  });

  describe('delete', () => {
    it('should delete schedule and remove cron job', async () => {
      mockScheduleRepository.delete.mockResolvedValue({ scheduleId: 1 });
      const jobMap = new Map();
      jobMap.set('schedule-1', {});
      mockSchedulerRegistry.getCronJobs.mockReturnValue(jobMap);

      const result = await service.delete(1);
      expect(mockSchedulerRegistry.deleteCronJob).toHaveBeenCalledWith('schedule-1');
      expect(mockScheduleRepository.delete).toHaveBeenCalledWith(1);
      expect(result).toEqual({ scheduleId: 1 });
    });
  });

  describe('getScheduleSuggestions', () => {
    it('should return AI suggestions falling back to mock when fetch fails', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));
      const result = await service.getScheduleSuggestions(1);
      expect(result.status).toBe('fallback');
    });

    it('should return parsed JSON when fetch is successful', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue({ suggestion: 'Clean at 10 AM' })
      });

      const result = await service.getScheduleSuggestions(1);
      expect(result).toEqual({ suggestion: 'Clean at 10 AM' });
    });
  });
});
