import { Controller, Get, Post, Put, Delete, Param, Body, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiBearerAuth } from '@nestjs/swagger';
import { ScheduleService } from '../services/schedule.service';
import { RankGuard } from 'src/common/guard/auth.guard';
import { GetUser } from 'src/common/decorator/get-user.decorator';
import { User } from 'src/modules/auth/models/user.model';
import { CreateScheduleDto } from '../dto/request/create-schedule.request.dto';
import { UpdateScheduleDto } from '../dto/request/update-schedule.request.dto';
import { ResponseScheduleListDto, ResponseScheduleDto } from '../dto/response/schedule.response.dto';

@ApiTags('Schedule')
@ApiBearerAuth()
@Controller('api/schedule')
export class ScheduleController {
  constructor(private readonly scheduleService: ScheduleService) {}

  @Get()
  @UseGuards(RankGuard)
  @ApiOperation({ summary: '내 전체 스케줄 조회', description: '현재 로그인한 유저의 모든 스케줄 목록을 조회합니다.' })
  @ApiResponse({ status: 200, type: ResponseScheduleListDto })
  async getSchedules(@GetUser() user: User) {
    const data = await this.scheduleService.findAllByUserId(user.userId);
    return { data };
  }

  @Post()
  @UseGuards(RankGuard)
  @ApiOperation({ summary: '새 스케줄 생성', description: '특정 모듈 동작에 대한 자동화 스케줄을 생성합니다.' })
  @ApiResponse({ status: 201, type: ResponseScheduleDto })
  async createSchedule(@GetUser() user: User, @Body() dto: CreateScheduleDto) {
    const data = await this.scheduleService.create(user.userId, dto);
    return { data };
  }

  @Put(':scheduleId')
  @UseGuards(RankGuard)
  @ApiOperation({ summary: '기존 스케줄 수정', description: '기존에 등록된 스케줄을 수정합니다.' })
  @ApiResponse({ status: 200, type: ResponseScheduleDto })
  async updateSchedule(@Param('scheduleId') scheduleId: string, @Body() dto: UpdateScheduleDto) {
    const data = await this.scheduleService.update(Number(scheduleId), dto);
    return { data };
  }

  @Delete(':scheduleId')
  @UseGuards(RankGuard)
  @ApiOperation({ summary: '스케줄 삭제', description: '등록된 스케줄을 영구적으로 삭제합니다.' })
  @ApiResponse({ status: 200 })
  async deleteSchedule(@Param('scheduleId') scheduleId: string) {
    await this.scheduleService.delete(Number(scheduleId));
    return { message: 'Schedule deleted successfully' };
  }
}
