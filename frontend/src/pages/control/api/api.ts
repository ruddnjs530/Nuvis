import type {
  WebRTCCandidateResponse,
  WebRTCConnectionResponse,
  WebRTCIceCandidate,
  WebRTCOfferResponse,
  WebRTCSdpData,
} from './types';
import { api } from '~/lib/api/client';

export const webrtcApi = {
  createConnection: (sessionId: string) =>
    api<WebRTCConnectionResponse>({
      apiPrefix: '',
      method: 'put',
      url: 'signaling/connection',
      options: { headers: { 'session-id': sessionId } },
    }),

  getOffers: (sessionId: string, fromtime: number) =>
    api<WebRTCOfferResponse>({
      apiPrefix: '',
      method: 'get',
      url: 'signaling/offer',
      options: {
        headers: { 'session-id': sessionId },
        searchParams: { fromtime: fromtime.toString() },
      },
    }),

  sendAnswer: (sessionId: string, data: WebRTCSdpData) =>
    api<{ message: string }>({
      apiPrefix: '',
      method: 'post',
      url: 'signaling/answer',
      options: {
        headers: { 'session-id': sessionId },
        json: data,
      },
    }),

  sendCandidate: (sessionId: string, data: { connectionId: string } & WebRTCIceCandidate) =>
    api<{ message: string }>({
      apiPrefix: '',
      method: 'post',
      url: 'signaling/candidate',
      options: {
        headers: { 'session-id': sessionId },
        json: data,
      },
    }),

  getCandidates: (sessionId: string, fromtime: number) =>
    api<WebRTCCandidateResponse>({
      apiPrefix: '',
      method: 'get',
      url: 'signaling/candidate',
      options: {
        headers: { 'session-id': sessionId },
        searchParams: { fromtime: fromtime.toString() },
      },
    }),
};
