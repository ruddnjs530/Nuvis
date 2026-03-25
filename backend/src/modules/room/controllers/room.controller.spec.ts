import { Test, TestingModule } from '@nestjs/testing';
import { RoomController } from './room.controller';
import { RoomService } from '../services/room.service';
import { User } from 'src/modules/auth/models/user.model';
import { RankGuard } from 'src/common/guard/auth.guard';

describe('RoomController', () => {
  let controller: RoomController;
  let service: RoomService;

  const mockRoomService = {
    getAllRoomNames: jest.fn(),
    getRoomData: jest.fn(),
    getRoomMaps: jest.fn(),
    applyDemoAction: jest.fn(),
  };

  const mockUser: User = { userId: 1, email: 'test@ssafy.com', name: 'Test User' };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [RoomController],
      providers: [
        { provide: RoomService, useValue: mockRoomService },
      ],
    })
    .overrideGuard(RankGuard)
    .useValue({ canActivate: jest.fn().mockReturnValue(true) })
    .compile();

    controller = module.get<RoomController>(RoomController);
    service = module.get<RoomService>(RoomService);
  });

  it('should call getRoomNames', async () => {
    (service.getAllRoomNames as jest.Mock).mockResolvedValue({ data: [] });
    await controller.getAllRoomNames(mockUser);
    expect(service.getAllRoomNames).toHaveBeenCalledWith(mockUser.userId);
  });

  it('should call getRoomData', async () => {
    (service.getRoomData as jest.Mock).mockResolvedValue({ data: [] });
    await controller.getRoomData(mockUser);
    expect(service.getRoomData).toHaveBeenCalledWith(mockUser.userId);
  });

  it('should call getRoomMaps', async () => {
    (service.getRoomMaps as jest.Mock).mockResolvedValue({ data: [] });
    await controller.getRoomMaps(mockUser);
    expect(service.getRoomMaps).toHaveBeenCalledWith(mockUser.userId);
  });

  it('should call applyDemoAction', async () => {
    (service.applyDemoAction as jest.Mock).mockResolvedValue({ success: true });
    await controller.applyDemoAction('1', 'heater');
    expect(service.applyDemoAction).toHaveBeenCalledWith(1, 'heater');
  });
});
