import { Test, TestingModule } from '@nestjs/testing';
import { WebrtcSignalingService } from './webrtc-signaling.service';

describe('WebrtcSignalingService', () => {
  let service: WebrtcSignalingService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [WebrtcSignalingService],
    }).compile();

    service = module.get<WebrtcSignalingService>(WebrtcSignalingService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('createSession & deleteSession', () => {
    it('should create a session returning sessionId', () => {
      const { sessionId } = service.createSession();
      expect(typeof sessionId).toBe('string');
      expect(sessionId.length).toBeGreaterThan(0);
    });

    it('should delete a created session', () => {
      const { sessionId } = service.createSession();
      expect(service.createConnection(sessionId)).toBeDefined();
      
      service.deleteSession(sessionId);
      expect(service.createConnection(sessionId)).toBeNull();
    });
  });

  describe('createConnection', () => {
    it('should return null if session is invalid', () => {
      expect(service.createConnection('invalid')).toBeNull();
    });

    it('should return connectionId when session exists', () => {
      const { sessionId } = service.createSession();
      const res = service.createConnection(sessionId);
      expect(res).toBeDefined();
      expect(res.connectionId).toBeDefined();
    });
  });

  describe('offers, answers, candidates', () => {
    let sessionId: string;
    
    beforeEach(() => {
      sessionId = service.createSession().sessionId;
    });

    it('should add and retrieve offers based on fromtime', async () => {
      service.addOffer(sessionId, { sdp: 'offer_1' });
      
      await new Promise(r => setTimeout(r, 50)); // artificial delay
      const currentTime = Date.now();
      
      service.addOffer(sessionId, { sdp: 'offer_2' });

      // get all
      const allOffers = service.getOffers(sessionId, 0);
      expect(allOffers.offers.length).toBe(2);

      // get only after currentTime
      const recentOffers = service.getOffers(sessionId, currentTime - 10);
      expect(recentOffers.offers.length).toBe(1);
      expect(recentOffers.offers[0].sdp).toBe('offer_2');
    });

    it('should add and retrieve answers based on fromtime', () => {
      service.addAnswer(sessionId, { sdp: 'ans' });
      const res = service.getAnswers(sessionId, 0);
      expect(res.answers.length).toBe(1);
      expect(res.answers[0].sdp).toBe('ans');
    });

    it('should add and retrieve candidates matching Unity container format', () => {
      service.addCandidate(sessionId, { connectionId: 'c1', candidate: 'c1_cand1' });
      service.addCandidate(sessionId, { connectionId: 'c1', candidate: 'c1_cand2' });
      service.addCandidate(sessionId, { connectionId: 'c2', candidate: 'c2_cand1' });

      const res = service.getCandidates(sessionId, 0);
      expect(res.candidates.length).toBe(2);
      
      const c1Obj = res.candidates.find(c => c.connectionId === 'c1');
      expect(c1Obj.candidates.length).toBe(2);
      
      const c2Obj = res.candidates.find(c => c.connectionId === 'c2');
      expect(c2Obj.candidates.length).toBe(1);
    });
  });
});
