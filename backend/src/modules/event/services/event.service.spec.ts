import { Test, TestingModule } from '@nestjs/testing';
import { EventService } from './event.service';
import { EventRepository } from '../repositories/event.repository';
import { RobotService } from '../../robot/services/robot.service';

describe('EventService', () => {
  let service: EventService;

  const mockEventRepository = {
    findAll: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
  };

  const mockRobotService = {
    getAiDataset: jest.fn(),
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        EventService,
        { provide: EventRepository, useValue: mockEventRepository },
        { provide: RobotService, useValue: mockRobotService },
      ],
    }).compile();

    service = module.get<EventService>(EventService);
    
    // Mock global fetch for getEventSuggestions
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('findAll', () => {
    it('should return all events for a user', async () => {
      const mockResult = [{ eventId: 1, name: 'event1' }];
      mockEventRepository.findAll.mockResolvedValue(mockResult);

      const result = await service.findAll(1);
      expect(mockEventRepository.findAll).toHaveBeenCalledWith(1);
      expect(result).toEqual(mockResult);
    });
  });

  describe('create', () => {
    it('should create an event', async () => {
      const mockDto = { roomId: 1, moduleType: 1 };
      const expected = { eventId: 2, ...mockDto };
      mockEventRepository.create.mockResolvedValue(expected);

      const result = await service.create(1, mockDto);
      expect(mockEventRepository.create).toHaveBeenCalledWith(1, mockDto);
      expect(result).toEqual(expected);
    });
  });

  describe('update', () => {
    it('should update an event', async () => {
      const mockDto = { moduleLevel: 3 };
      const expected = { eventId: 1, ...mockDto };
      mockEventRepository.update.mockResolvedValue(expected);

      const result = await service.update(1, 100, mockDto);
      // userId is 100, eventId is 1 in param order: update(eventId, userId, dto)
      expect(mockEventRepository.update).toHaveBeenCalledWith(1, 100, mockDto);
      expect(result).toEqual(expected);
    });
  });

  describe('remove', () => {
    it('should delete an event', async () => {
      const expected = { eventId: 1 };
      mockEventRepository.delete.mockResolvedValue(expected);

      const result = await service.remove(1, 100);
      expect(mockEventRepository.delete).toHaveBeenCalledWith(1, 100);
      expect(result).toEqual(expected);
    });
  });

  describe('getEventSuggestions', () => {
    it('should return payload from AI server on successful fetch', async () => {
      const mockDataset = { data: 'test' };
      mockRobotService.getAiDataset.mockResolvedValue(mockDataset);

      const mockAiResponse = { suggestion: 'Turn on heater' };
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: jest.fn().mockResolvedValue(mockAiResponse),
      });

      const result = await service.getEventSuggestions(1);
      expect(mockRobotService.getAiDataset).toHaveBeenCalledWith(1, 14);
      expect(global.fetch).toHaveBeenCalled();
      expect(result).toEqual(mockAiResponse);
    });

    it('should return fallback payload if fetch fails', async () => {
      mockRobotService.getAiDataset.mockResolvedValue({});
      (global.fetch as jest.Mock).mockResolvedValue({ ok: false, status: 500 });

      const result = await service.getEventSuggestions(1);
      
      expect(result.status).toBe('fallback');
      expect(result.message).toContain('AI');
    });
  });
});
