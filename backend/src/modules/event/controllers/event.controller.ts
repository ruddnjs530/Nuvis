import { Controller, Get, Post, Put, Delete, Body, Param, UseGuards, ParseIntPipe } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiBearerAuth } from '@nestjs/swagger';
import { EventService } from '../services/event.service';
import { CreateEventDto } from '../dto/request/create-event.dto';
import { UpdateEventDto } from '../dto/request/update-event.dto';
import { ResponseEventListDto, ResponseEventSingleDto } from '../dto/response/response-event.dto';
import { RankGuard } from 'src/common/guard/auth.guard';
import { GetUser } from 'src/common/decorator/get-user.decorator';
import { User } from 'src/modules/auth/models/user.model';

@ApiTags('Events')
@ApiBearerAuth()
@Controller('api/event')
@UseGuards(RankGuard)
export class EventController {
  constructor(private readonly eventService: EventService) {}

  @ApiOperation({ summary: '자동화 이벤트 목록 조회', description: '현재 사용자가 등록한 모든 이벤트 규칙을 조회합니다.' })
  @ApiResponse({ status: 200, description: '성공적으로 조회되었습니다.', type: ResponseEventListDto })
  @Get()
  async findAll(@GetUser() user: User) {
    const data = await this.eventService.findAll(user.userId);
    return { data };
  }

  @ApiOperation({ summary: '자동화 이벤트 생성', description: '새로운 이벤트 규칙을 등록합니다.' })
  @ApiResponse({ status: 201, description: '성공적으로 생성되었습니다.', type: ResponseEventSingleDto })
  @Post()
  async create(@GetUser() user: User, @Body() createEventDto: CreateEventDto) {
    const data = await this.eventService.create(user.userId, createEventDto);
    return { data };
  }

  @ApiOperation({ summary: '자동화 이벤트 수정', description: '기존에 등록된 이벤트 규칙을 수정합니다.' })
  @ApiResponse({ status: 200, description: '성공적으로 수정되었습니다.', type: ResponseEventSingleDto })
  @Put(':eventId')
  async update(
    @GetUser() user: User,
    @Param('eventId', ParseIntPipe) eventId: number,
    @Body() updateEventDto: UpdateEventDto,
  ) {
    const data = await this.eventService.update(eventId, user.userId, updateEventDto);
    return { data };
  }

  @ApiOperation({ summary: '자동화 이벤트 삭제', description: '이벤트 규칙을 삭제합니다.' })
  @ApiResponse({ status: 200, description: '성공적으로 삭제되었습니다.', type: ResponseEventSingleDto })
  @Delete(':eventId')
  async remove(
    @GetUser() user: User,
    @Param('eventId', ParseIntPipe) eventId: number,
  ) {
    const data = await this.eventService.remove(eventId, user.userId);
    return { data };
  }
}
