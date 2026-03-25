import { Test, TestingModule } from '@nestjs/testing';
import { WebrtcSignalingController } from './webrtc-signaling.controller';
import { WebrtcSignalingService } from '../services/webrtc-signaling.service';
import { BadRequestException } from '@nestjs/common';

describe('WebrtcSignalingController', () => {
  let controller: WebrtcSignalingController;
  let service: WebrtcSignalingService;

  const mockSignalingService = {
    createSession: jest.fn(),
    deleteSession: jest.fn(),
    createConnection: jest.fn(),
    addOffer: jest.fn(),
    getOffers: jest.fn(),
    addAnswer: jest.fn(),
    getAnswers: jest.fn(),
    addCandidate: jest.fn(),
    getCandidates: jest.fn(),
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [WebrtcSignalingController],
      providers: [
        { provide: WebrtcSignalingService, useValue: mockSignalingService },
      ],
    }).compile();

    controller = module.get<WebrtcSignalingController>(WebrtcSignalingController);
    service = module.get<WebrtcSignalingService>(WebrtcSignalingService);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  describe('Session Management', () => {
    it('createSession should return sessionId', () => {
      mockSignalingService.createSession.mockReturnValue({ sessionId: '123' });
      expect(controller.createSession()).toEqual({ sessionId: '123' });
    });

    it('deleteSession should call service delete', () => {
      const res = controller.deleteSession('123');
      expect(service.deleteSession).toHaveBeenCalledWith('123');
      expect(res).toEqual({ message: 'ok' });
    });

    it('deleteSession should skip if no header element exists', () => {
      controller.deleteSession(undefined);
      expect(service.deleteSession).not.toHaveBeenCalled();
    });

    it('createConnection should return connectionId', () => {
      mockSignalingService.createConnection.mockReturnValue({ connectionId: 'conn-1' });
      expect(controller.createConnection('123')).toEqual({ connectionId: 'conn-1' });
      expect(service.createConnection).toHaveBeenCalledWith('123');
    });

    it('createConnection should throw BadRequest if session invalid', () => {
      mockSignalingService.createConnection.mockReturnValue(null);
      expect(() => controller.createConnection('bad')).toThrow(BadRequestException);
    });
  });

  describe('SDP & Candidate Polling', () => {
    it('should add offer', () => {
      const res = controller.createOffer('123', { type: 'offer' });
      expect(service.addOffer).toHaveBeenCalledWith('123', { type: 'offer' });
      expect(res).toEqual({ message: 'ok' });
    });

    it('should get offers casting fromtime', () => {
      mockSignalingService.getOffers.mockReturnValue({ offers: [] });
      controller.getOffers('123', '500');
      expect(service.getOffers).toHaveBeenCalledWith('123', 500);
    });

    it('should add answer', () => {
      const res = controller.createAnswer('123', { type: 'answer' });
      expect(service.addAnswer).toHaveBeenCalledWith('123', { type: 'answer' });
      expect(res).toEqual({ message: 'ok' });
    });

    it('should get answers', () => {
      controller.getAnswers('123', '0');
      expect(service.getAnswers).toHaveBeenCalledWith('123', 0);
    });

    it('should add candidate', () => {
      const res = controller.createCandidate('123', { candidate: 'cand' });
      expect(service.addCandidate).toHaveBeenCalledWith('123', { candidate: 'cand' });
      expect(res).toEqual({ message: 'ok' });
    });

    it('should get candidates', () => {
      controller.getCandidates('123', undefined);
      // undefined should parse to 0
      expect(service.getCandidates).toHaveBeenCalledWith('123', 0);
    });
  });
});
