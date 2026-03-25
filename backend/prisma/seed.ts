import { PrismaClient } from '@prisma/client';
import * as bcrypt from 'bcrypt';

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

  // 2. Create targetZone mapping according to ROS2 waypoints.yaml
  const roomsData = [
    { name: '스테이션 (HQ)', targetZone: 'hq' },
    { name: '거실', targetZone: 'living_room' },
    { name: '침실', targetZone: 'bedroom' },
    { name: '주방', targetZone: 'kitchen' },
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

  // 3. (Optional) Create a default registered Robot and Module
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
