import { Controller, Put, Post, Get, Delete, Body, Query, Headers, BadRequestException, HttpCode } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { WebrtcSignalingService } from '../services/webrtc-signaling.service';

@ApiTags('WebRTC Signaling')
@Controller('signaling')
export class WebrtcSignalingController {
  constructor(private readonly signalingService: WebrtcSignalingService) {}

  @Put()
  @ApiOperation({ summary: 'Create WebRTC Session (Unity HTTP Signaling Protocol)' })
  createSession() {
    return this.signalingService.createSession();
  }

  @Delete()
  @ApiOperation({ summary: 'Delete WebRTC Session' })
  deleteSession(@Headers('session-id') sessionId: string) {
    if (!sessionId) return { message: 'ok' };
    this.signalingService.deleteSession(sessionId);
    return { message: 'ok' };
  }

  @Put('connection')
  @ApiOperation({ summary: 'Create WebRTC Connection ID' })
  createConnection(@Headers('session-id') sessionId: string) {
    const res = this.signalingService.createConnection(sessionId);
    if (!res) throw new BadRequestException('Invalid Session-Id Header');
    return res;
  }

  @Post('offer')
  @HttpCode(200)
  @ApiOperation({ summary: 'Store WebRTC Offer SDP' })
  createOffer(@Headers('session-id') sessionId: string, @Body() body: any) {
    this.signalingService.addOffer(sessionId, body);
    return { message: 'ok' };
  }

  @Get('offer')
  @ApiOperation({ summary: 'Retrieve WebRTC Offers based on fromtime polling' })
  getOffers(@Headers('session-id') sessionId: string, @Query('fromtime') fromtime: string) {
    const time = parseInt(fromtime || '0', 10);
    return this.signalingService.getOffers(sessionId, time);
  }

  @Post('answer')
  @HttpCode(200)
  @ApiOperation({ summary: 'Store WebRTC Answer SDP' })
  createAnswer(@Headers('session-id') sessionId: string, @Body() body: any) {
    this.signalingService.addAnswer(sessionId, body);
    return { message: 'ok' };
  }

  @Get('answer')
  @ApiOperation({ summary: 'Retrieve WebRTC Answers based on fromtime polling' })
  getAnswers(@Headers('session-id') sessionId: string, @Query('fromtime') fromtime: string) {
    const time = parseInt(fromtime || '0', 10);
    return this.signalingService.getAnswers(sessionId, time);
  }

  @Post('candidate')
  @HttpCode(200)
  @ApiOperation({ summary: 'Store WebRTC ICE Candidate' })
  createCandidate(@Headers('session-id') sessionId: string, @Body() body: any) {
    this.signalingService.addCandidate(sessionId, body);
    return { message: 'ok' };
  }

  @Get('candidate')
  @ApiOperation({ summary: 'Retrieve WebRTC ICE Candidates' })
  getCandidates(@Headers('session-id') sessionId: string, @Query('fromtime') fromtime: string) {
    const time = parseInt(fromtime || '0', 10);
    return this.signalingService.getCandidates(sessionId, time);
  }
}
