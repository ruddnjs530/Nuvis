import { Test, TestingModule } from '@nestjs/testing';
import { EventController } from './event.controller';
import { EventService } from '../services/event.service';
import { User } from 'src/modules/auth/models/user.model';
import { CreateEventDto } from '../dto/request/create-event.dto';
import { UpdateEventDto } from '../dto/request/update-event.dto';
import { RankGuard } from 'src/common/guard/auth.guard';

describe('EventController', () => {
  let controller: EventController;
  let service: EventService;

  const mockEventService = {
    findAll: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    remove: jest.fn(),
  };

  const mockUser: User = { userId: 1, email: 'usr@test.com', name: 'user' };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [EventController],
      providers: [
        { provide: EventService, useValue: mockEventService },
      ],
    })
    .overrideGuard(RankGuard)
    .useValue({ canActivate: jest.fn().mockReturnValue(true) })
    .compile();

    controller = module.get<EventController>(EventController);
    service = module.get<EventService>(EventService);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  describe('findAll', () => {
    it('should wrap service result in data object', async () => {
      const expected = [{ eventId: 1 }];
      (service.findAll as jest.Mock).mockResolvedValue(expected);

      const result = await controller.findAll(mockUser);
      expect(service.findAll).toHaveBeenCalledWith(mockUser.userId);
      expect(result).toEqual({ data: expected });
    });
  });

  describe('create', () => {
    it('should return wrapped newly created event', async () => {
      const dto = new CreateEventDto();
      const expected = { eventId: 2 };
      (service.create as jest.Mock).mockResolvedValue(expected);

      const result = await controller.create(mockUser, dto);
      expect(service.create).toHaveBeenCalledWith(mockUser.userId, dto);
      expect(result).toEqual({ data: expected });
    });
  });

  describe('update', () => {
    it('should return wrapped updated event', async () => {
      const dto = new UpdateEventDto();
      const expected = { eventId: 1 };
      (service.update as jest.Mock).mockResolvedValue(expected);

      const result = await controller.update(mockUser, 1, dto);
      expect(service.update).toHaveBeenCalledWith(1, mockUser.userId, dto);
      expect(result).toEqual({ data: expected });
    });
  });

  describe('remove', () => {
    it('should return wrapped deleted event', async () => {
      const expected = { eventId: 1 };
      (service.remove as jest.Mock).mockResolvedValue(expected);

      const result = await controller.remove(mockUser, 1);
      expect(service.remove).toHaveBeenCalledWith(1, mockUser.userId);
      expect(result).toEqual({ data: expected });
    });
  });
});
