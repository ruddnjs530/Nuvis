import type {
  WebRTCAnswerResponse,
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
      method: 'put',
      url: 'signaling/connection',
      options: { headers: { 'session-id': sessionId } },
    }),

  getOffers: (sessionId: string, fromtime: number) =>
    api<WebRTCOfferResponse>({
      method: 'get',
      url: 'signaling/offer',
      options: {
        headers: { 'session-id': sessionId },
        searchParams: { fromtime: fromtime.toString() },
      },
    }),

  sendAnswer: (sessionId: string, data: WebRTCSdpData) =>
    api<{ message: string }>({
      method: 'post',
      url: 'signaling/answer',
      options: {
        headers: { 'session-id': sessionId },
        json: data,
      },
    }),

  sendCandidate: (sessionId: string, data: { connectionId: string } & WebRTCIceCandidate) =>
    api<{ message: string }>({
      method: 'post',
      url: 'signaling/candidate',
      options: {
        headers: { 'session-id': sessionId },
        json: data,
      },
    }),

  getCandidates: (sessionId: string, fromtime: number) =>
    api<WebRTCCandidateResponse>({
      method: 'get',
      url: 'signaling/candidate',
      options: {
        headers: { 'session-id': sessionId },
        searchParams: { fromtime: fromtime.toString() },
      },
    }),

  sendOffer: (sessionId: string, data: WebRTCSdpData) =>
    api<{ message: string }>({
      method: 'post',
      url: 'signaling/offer',
      options: {
        headers: { 'session-id': sessionId },
        json: data,
      },
    }),

  getAnswers: (sessionId: string, fromtime: number) =>
    api<WebRTCAnswerResponse>({
      method: 'get',
      url: 'signaling/answer',
      options: {
        headers: { 'session-id': sessionId },
        searchParams: { fromtime: fromtime.toString() },
      },
    }),
};
