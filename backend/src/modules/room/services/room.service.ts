import { Injectable } from '@nestjs/common';
import { RoomNameListResponseDto } from '../dto/response/room-name.response.dto';
import { RoomDataListResponseDto, RoomConditionDto } from '../dto/response/room-data.response.dto';
import { RoomMapListResponseDto } from '../dto/response/room-map.response.dto';
import { RoomRepository } from '../repositories/room.repository';

interface RoomState {
  condition: RoomConditionDto | null;
  lockedUntil: number; // timestamp until the values are fixed
}

@Injectable()
export class RoomService {
  private readonly roomStates = new Map<number, RoomState>();

  constructor(private readonly roomRepository: RoomRepository) {}

  create(data: any) {
    return { ...data, roomId: Date.now() };
  }

  async getAllRoomNames(userId: number): Promise<RoomNameListResponseDto> {
    const rooms = await this.roomRepository.findAllNames(userId);
    return { data: rooms };
  }

  async getRoomData(userId: number): Promise<RoomDataListResponseDto> {
    const rooms = await this.roomRepository.findAllNames(userId);
    const now = Date.now();

    const data = rooms.map((room) => {
      let state = this.roomStates.get(room.roomId);

      // 1. 방 상태가 아직 인메모리에 없다면 완전 초기화
      if (!state) {
        const isNull = Math.random() > 0.8;
        state = {
          condition: isNull ? null : {
            temperature: parseFloat((Math.random() * (30 - 18) + 18).toFixed(1)),
            humidity: parseFloat((Math.random() * (70 - 30) + 30).toFixed(1)),
            fineDust: parseFloat((Math.random() * (100 - 10) + 10).toFixed(1)),
            updatedAt: new Date(),
          },
          lockedUntil: 0,
        };
        this.roomStates.set(room.roomId, state);
      } else if (state.condition) {
        // 2. 이미 값이 있다면, 모듈 가동 중(Lock)이 아닐 때만 약간씩 센서 값을 무작위로 흔듦 (자연스러운 환경 변화 연출)
        if (now > state.lockedUntil) {
          state.condition.temperature += parseFloat((Math.random() * 0.4 - 0.2).toFixed(1)); // -0.2 ~ +0.2
          state.condition.humidity += parseFloat((Math.random() * 2.0 - 1.0).toFixed(1)); // -1.0 ~ +1.0
          state.condition.fineDust += parseFloat((Math.random() * 4.0 - 2.0).toFixed(1)); // -2.0 ~ +2.0
          
          // 범위 보정
          state.condition.temperature = Math.max(10, Math.min(35, state.condition.temperature));
          state.condition.humidity = Math.max(10, Math.min(90, state.condition.humidity));
          state.condition.fineDust = Math.max(0, Math.min(200, state.condition.fineDust));
          state.condition.updatedAt = new Date();
        }
      }

      return {
        ...room,
        condition: state.condition,
      };
    });

    return { data };
  }

  async getRoomMaps(userId: number): Promise<RoomMapListResponseDto> {
    const rooms = await this.roomRepository.findAllMaps(userId);

    const data = rooms.map((room) => {
      // DB에 mapData가 없으면 Unity 연동 데모를 위해 기본(MOCK) 맵 데이터 제공
      let mapData = room.mapData;
      if (!mapData) {
        mapData = {
          resolution: 0.05,
          origin: { x: -10.0, y: -10.0, theta: 0.0 },
          mapImageUrl: `https://dummyimage.com/4000x4000/cccccc/000000&text=${encodeURIComponent(room.name + ' Map')}`,
          // MOCK: Generate some arbitrary box coordinates based on roomId
          boundaries: [
            { x: room.roomId * 2.0, y: 1.0 },
            { x: room.roomId * 2.0 + 2.0, y: 1.0 },
            { x: room.roomId * 2.0 + 2.0, y: -1.0 },
            { x: room.roomId * 2.0, y: -1.0 }
          ],
          centerPoint: { x: room.roomId * 2.0 + 1.0, y: 0.0, theta: 0.0 }
        };
      }

      return {
        roomId: room.roomId,
        name: room.name,
        mapData: mapData as any,
      };
    });

    return { data };
  }

  // 데모 시뮬레이터를 위한 모듈 가동 에뮬레이팅 메서드
  async applyDemoAction(roomId: number, actionType: string) {
    let state = this.roomStates.get(roomId);
    if (!state || !state.condition) {
      // 강제 초기화
      state = {
        condition: {
          temperature: 24.0, humidity: 45.0, fineDust: 30.0, updatedAt: new Date()
        },
        lockedUntil: 0
      };
    }

    // 모듈 가동 시 5분(300000ms) 동안 수치 고정
    const lockDuration = 5 * 60 * 1000;
    state.lockedUntil = Date.now() + lockDuration;
    
    // We forcefully initialized condition above, so it can't be null here
    const condition = state.condition!;

    switch (actionType) {
      case 'air_purifier':
        condition.fineDust = 8.0; // 맑음
        break;
      case 'humidifier':
        condition.humidity = 65.0; // 촉촉함
        break;
      case 'dehumidifier':
        condition.humidity = 35.0; // 건조함
        break;
      case 'heater':
        condition.temperature = 28.0; // 따뜻함
        break;
      case 'cooler':
        condition.temperature = 18.0; // 시원함
        break;
    }
    
    condition.updatedAt = new Date();
    this.roomStates.set(roomId, state);
    
    return { success: true, message: `${actionType} 가동 시뮬레이션 적용됨. 5분간 수치 고정.`, condition: state.condition };
  }
}
