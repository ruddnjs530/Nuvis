import { Injectable, Logger } from '@nestjs/common';
import { randomUUID } from 'crypto';

interface SessionData {
  sessionId: string;
  connections: string[];
  offers: { timestamp: number; data: any }[];
  answers: { timestamp: number; data: any }[];
  candidates: { timestamp: number; data: any }[];
  createdAt: number;
}

@Injectable()
export class WebrtcSignalingService {
  private readonly logger = new Logger(WebrtcSignalingService.name);
  private sessions = new Map<string, SessionData>();

  createSession(): { sessionId: string } {
    const sessionId = randomUUID();
    this.sessions.set(sessionId, {
      sessionId,
      connections: [],
      offers: [],
      answers: [],
      candidates: [],
      createdAt: Date.now(),
    });
    this.logger.log(`Session created: ${sessionId}`);
    
    // 주기적으로 2시간 지난 오래된 세션 삭제 (메모리 릭 방지)
    this.cleanup();
    
    return { sessionId };
  }

  deleteSession(sessionId: string) {
    if (this.sessions.has(sessionId)) {
      this.sessions.delete(sessionId);
      this.logger.log(`Session deleted: ${sessionId}`);
    }
  }

  createConnection(sessionId: string): { connectionId: string } | null {
    const session = this.sessions.get(sessionId);
    if (!session) return null;

    const connectionId = randomUUID();
    session.connections.push(connectionId);
    this.logger.log(`Connection created: ${connectionId} for session: ${sessionId}`);
    return { connectionId };
  }

  addOffer(sessionId: string, data: any) {
    const session = this.sessions.get(sessionId);
    if (session) {
      session.offers.push({ timestamp: Date.now(), data });
    }
  }

  getOffers(sessionId: string, fromtime: number): any {
    const session = this.sessions.get(sessionId);
    if (!session) return { offers: [] };
    const offers = session.offers.filter(o => o.timestamp > fromtime).map(o => o.data);
    return { offers };
  }

  addAnswer(sessionId: string, data: any) {
    const session = this.sessions.get(sessionId);
    if (session) {
      session.answers.push({ timestamp: Date.now(), data });
    }
  }

  getAnswers(sessionId: string, fromtime: number): any {
    const session = this.sessions.get(sessionId);
    if (!session) return { answers: [] };
    const answers = session.answers.filter(o => o.timestamp > fromtime).map(o => o.data);
    return { answers };
  }

  addCandidate(sessionId: string, data: any) {
    const session = this.sessions.get(sessionId);
    if (session) {
      session.candidates.push({ timestamp: Date.now(), data });
    }
  }

  getCandidates(sessionId: string, fromtime: number): any {
    const session = this.sessions.get(sessionId);
    if (!session) return { candidates: [] };
    
    // Unity HttpSignaling 프로토콜 구조에 맞게 매핑:
    // { "candidates": [ { "connectionId": "...", "candidates": [ { candidate details } ] } ] }
    const newCands = session.candidates.filter(c => c.timestamp > fromtime).map(c => c.data);
    
    const byConnection: Record<string, any[]> = {};
    for (const c of newCands) {
      const cid = c.connectionId;
      if (!byConnection[cid]) byConnection[cid] = [];
      byConnection[cid].push(c);
    }

    const containers = Object.keys(byConnection).map(cid => ({
      connectionId: cid,
      candidates: byConnection[cid]
    }));

    return { candidates: containers };
  }

  private cleanup() {
    const now = Date.now();
    for (const [id, session] of this.sessions.entries()) {
      if (now - session.createdAt > 1000 * 60 * 60 * 2) {
        this.sessions.delete(id);
      }
    }
  }
}
