import { Test, TestingModule } from '@nestjs/testing';
import { RoomService } from './room.service';
import { RoomRepository } from '../repositories/room.repository';

describe('RoomService', () => {
  let service: RoomService;
  let repository: RoomRepository;

  const mockRoomRepository = {
    findAllNames: jest.fn(),
    findAllMaps: jest.fn(),
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        RoomService,
        { provide: RoomRepository, useValue: mockRoomRepository },
      ],
    }).compile();

    service = module.get<RoomService>(RoomService);
    repository = module.get<RoomRepository>(RoomRepository);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('getAllRoomNames', () => {
    it('should return room names successfully', async () => {
      const mockRooms = [{ roomId: 1, name: 'Living Room', targetZone: 'living_room' }];
      (repository.findAllNames as jest.Mock).mockResolvedValue(mockRooms);

      const result = await service.getAllRoomNames(1);
      
      expect(repository.findAllNames).toHaveBeenCalledWith(1);
      expect(result).toEqual({ data: mockRooms });
    });
  });

  describe('getRoomMaps', () => {
    it('should return mock mapData if none exists in db', async () => {
      const mockRooms = [{ roomId: 1, name: 'HQ', mapData: null }];
      (repository.findAllMaps as jest.Mock).mockResolvedValue(mockRooms);

      const result = await service.getRoomMaps(1);

      expect(repository.findAllMaps).toHaveBeenCalledWith(1);
      expect(result.data[0].mapData).toBeDefined();
      expect(result.data[0].mapData!.resolution).toBe(0.05);
      expect(result.data[0].mapData!.centerPoint).toEqual({ x: 3, y: 0, theta: 0 }); // roomId=1 => 2*1+1 = 3
    });
  });

  describe('applyDemoAction', () => {
    it('should lock room conditions for 5 minutes and update properly', async () => {
      const res = await service.applyDemoAction(1, 'air_purifier');
      
      expect(res.success).toBe(true);
      expect(res.condition.fineDust).toBe(8.0);
    });
  });

  describe('getRoomData', () => {
    it('should assign and update random sensor values', async () => {
      const mockRooms = [{ roomId: 1, name: 'Room' }];
      (repository.findAllNames as jest.Mock).mockResolvedValue(mockRooms);

      // first call initializes mock data
      const res1 = await service.getRoomData(1);
      expect(res1.data.length).toBe(1);
      
      // Since condition can be null 20% of the time, we might need to handle it.
      // applyDemoAction forces initialization:
      await service.applyDemoAction(1, 'heater');
      
      const res2 = await service.getRoomData(1);
      expect(res2.data[0].condition).toBeDefined();
      expect(res2.data[0].condition.temperature).toBe(28.0); // heater lock
    });
  });
});
