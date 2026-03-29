import { PrismaClient } from '@prisma/client';
import * as bcrypt from 'bcrypt';
import * as fs from 'fs';
import * as path from 'path';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Seeding the database with initial Unity Map data...');

  // 1. Create a default User
  const passwordHash = await bcrypt.hash('12345678', 10);
  const user = await prisma.user.upsert({
    where: { email: 'admin@ssafy.com' },
    update: {},
    create: {
      email: 'admin@ssafy.com',
      name: 'Admin User',
      passwordHash,
    },
  });

  console.log(`User created: ${user.email} (ID: ${user.userId})`);

  // 2. Create targetZone mapping according to ROS2 rooms.yaml AND AI STT hardcoded map
  const roomsData = [
    { name: '스테이션 (HQ)', targetZone: 'hq' },                   // ID 1
    { name: '거실', targetZone: 'tv' },                            // ID 2
    { name: '침실1 (좌측 상단)', targetZone: 'left_up_room' },       // ID 3 (STT: 침실)
    { name: '주방', targetZone: 'kitchen' },                       // ID 4
    { name: '침실2 (좌측 하단)', targetZone: 'left_down_room' },     // ID 5
    { name: 'PC방', targetZone: 'pc' },                            // ID 6
    { name: '현관', targetZone: 'entrance' },                      // ID 7
    { name: '현관 옆방', targetZone: 'entrance_next_room' },          // ID 8
    { name: '화장실 옆방', targetZone: 'toilet_next_room' },          // ID 9
  ];

  for (const { name, targetZone } of roomsData) {
    const existing = await prisma.room.findFirst({
      where: { userId: user.userId, targetZone },
    });

    if (!existing) {
      await prisma.room.create({
        data: {
          userId: user.userId,
          name,
          targetZone,
        },
      });
      console.log(`Created Room: ${name} mapping to zone: ${targetZone}`);
    } else {
      console.log(`Room already exists for zone: ${targetZone}`);
    }
  }

  // 3. Seed Module Types
  const modulesData = [
    { moduleId: 1, type: 'AIR_PURIFIER', status: 'IDLE' },
    { moduleId: 2, type: 'HUMIDIFIER', status: 'IDLE' },
    { moduleId: 3, type: 'DEHUMIDIFIER', status: 'IDLE' },
    { moduleId: 4, type: 'STERILIZER', status: 'IDLE' },
    { moduleId: 5, type: 'DIFFUSER', status: 'IDLE' },
  ];

  for (const mod of modulesData) {
    await prisma.module.upsert({
      where: { moduleId: mod.moduleId },
      update: {},
      create: {
        moduleId: mod.moduleId,
        type: mod.type,
        status: mod.status,
      },
    });
  }
  console.log(`✅ ${modulesData.length} Modules seeded.`);

  // 4. (Optional) Create a default registered Robot and Module
  const existingRobot = await prisma.robot.findFirst({
    where: { userId: user.userId },
  });

  if (!existingRobot) {
    await prisma.robot.create({
      data: {
        userId: user.userId,
        status: 'IDLE',
        batteryLevel: 100.0,
      },
    });
    console.log(`Created a default Robot for user ${user.userId}`);
  }

  // 4. Seed mock sensor history (mock_payload.json → ROOM_CONDITIONS_HISTORY)
  const existingHistoryCount = await prisma.roomConditionHistory.count();
  if (existingHistoryCount === 0) {
    const filePath = path.join(__dirname, '..', 'src', 'modules', 'robot', 'data', 'mock_payload.json');
    const raw = fs.readFileSync(filePath, 'utf-8');
    const mock = JSON.parse(raw) as {
      sensor_data: {
        timestamp: string;
        room_id: number;
        temperature: number;
        humidity: number;
        fine_dust: number;
      }[];
    };

    // mock_payload room_id(2) → seed에서 생성된 거실의 실제 roomId를 조회
    const livingRoom = await prisma.room.findFirst({
      where: { userId: user.userId, targetZone: 'tv' },
    });

    if (!livingRoom) {
      console.warn('⚠️ 거실 Room을 찾지 못해 센서 이력 시딩을 건너뜁니다.');
    } else {
      const records = mock.sensor_data.map((row) => ({
        roomId: livingRoom.roomId,
        temperature: row.temperature,
        humidity: row.humidity,
        fineDust: row.fine_dust,
        recordedAt: new Date(row.timestamp),
      }));

      await prisma.roomConditionHistory.createMany({ data: records });
      console.log(`✅ ${records.length}건의 센서 이력을 DB에 삽입했습니다.`);
    }
  } else {
    console.log(`센서 이력이 이미 ${existingHistoryCount}건 존재합니다. 시딩을 건너뜁니다.`);
  }

  console.log('✅ Database seeded successfully!');
}

main()
  .catch((e) => {
    console.error('Seed failed:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });

