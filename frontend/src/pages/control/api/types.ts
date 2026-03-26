export interface WebRTCConnectionResponse {
  connectionId: string;
}

export interface WebRTCSdpData {
  connectionId: string;
  sdp: string;
}

export interface WebRTCOfferResponse {
  offers: WebRTCSdpData[];
}

export interface WebRTCAnswerResponse {
  answers: WebRTCSdpData[];
}

export interface WebRTCIceCandidate {
  candidate: string;
  sdpMLineIndex: number | null;
  sdpMid: string | null;
}

export interface WebRTCCandidateData {
  connectionId: string;
  candidates: WebRTCIceCandidate[];
}

export interface WebRTCCandidateResponse {
  candidates: WebRTCCandidateData[];
}
