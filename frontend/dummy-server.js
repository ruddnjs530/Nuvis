import http from 'node:http';

const PORT = 3000;

// ==========================================
// MOCK DATA STORE
// ==========================================
let events = [
  { eventId: 1, roomId: 1, actionModuleType: 'AIR_PURIFIER', conditionType: 'FINE_DUST', conditionOperator: 'GT', thresholdValue: 50, isActive: true },
  { eventId: 2, roomId: 2, actionModuleType: 'HUMIDIFIER', conditionType: 'HUMIDITY', conditionOperator: 'LT', thresholdValue: 40, isActive: false },
];
let nextEventId = 3;

let schedules = [
  { scheduleId: 1, userId: 1, roomId: 1, actionModuleType: 'AIR_PURIFIER',
    actionModulePower: true, actionModuleLevel: 2,
    startTime: '1970-01-01T08:30:00.000Z', durationMinutes: 60, isActive: true },
  { scheduleId: 2, userId: 1, roomId: 2, actionModuleType: 'HUMIDIFIER',
    actionModulePower: false, actionModuleLevel: 1,
    startTime: '1970-01-01T22:00:00.000Z', durationMinutes: 30, isActive: false },
];
let nextScheduleId = 3;

const rooms = [
  { roomId: 1, name: '거실', condition: { temperature: 24, humidity: 45, fineDust: 30, updatedAt: new Date().toISOString() } },
  { roomId: 2, name: '침실', condition: { temperature: 22, humidity: 55, fineDust: 15, updatedAt: new Date().toISOString() } },
  { roomId: 3, name: '부엌', condition: { temperature: 25, humidity: 60, fineDust: 80, updatedAt: new Date().toISOString() } },
];

const roomMaps = [
  { roomId: 1, name: '거실', mapData: { width: 4000, height: 4000, resolution: 0.05, origin: { x: -10.0, y: -10.0, theta: 0.0 }, mapImageUrl: 'https://dummyimage.com/4000x4000/cccccc/000000&text=Living+Room+Map' } },
  { roomId: 2, name: '침실', mapData: { width: 1024, height: 1024, resolution: 0.05, origin: { x: -5.0, y: -2.0, theta: 0.0 }, mapImageUrl: 'https://dummyimage.com/1024x1024/cccccc/000000&text=Bedroom+Map' } },
  { roomId: 3, name: '부엌', mapData: { width: 1024, height: 1024, resolution: 0.05, origin: { x: 0.0, y: 0.0, theta: 0.0 }, mapImageUrl: 'https://dummyimage.com/1024x1024/cccccc/000000&text=Kitchen+Map' } },
];

let robotStatus = {
  robotId: 'robot-01',
  mode: 0,
  taskState: 0,
  activeTaskId: '',
  batteryPct: 85.5,
  isCharging: false,
  safetyState: 0,
  lastErrorCode: 0,
  pose: { x: 0.5, y: 0.5, yaw: 0.0 },
  stamp: new Date().toISOString()
};


// ==========================================
// REQUEST HANDLER UTILS
// ==========================================
const parseBody = (req) => new Promise((resolve, reject) => {
  let body = '';
  req.on('data', chunk => body += chunk.toString());
  req.on('end', () => {
    try { resolve(body ? JSON.parse(body) : {}); }
    catch (e) { reject(e); }
  });
});

const sendJson = (res, statusCode, data) => {
  res.writeHead(statusCode, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(data));
};

// ==========================================
// SERVER
// ==========================================
const server = http.createServer(async (req, res) => {
  // CORS Headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, GET, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  const url = new URL(req.url, `http://localhost:${PORT}`);
  const method = req.method;
  const path = url.pathname.replace(/^\/api\/v1/, '/api'); // Normalize /api/v1 to /api

  console.log(`[${method}] ${path}`);

  try {
    // ----------------------------------------------------
    // AUTH
    // ----------------------------------------------------
    if (path === '/api/auth/login' && method === 'POST') {
      const body = await parseBody(req);
      const EXPECTED_HASH = '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4'; // 1234
      
      if (!body.email || !body.pw) return sendJson(res, 400, { message: 'Bad Request' });
      if (body.email === 'admin@ssafy.com' && body.pw === EXPECTED_HASH) {
        return sendJson(res, 200, { data: { accessToken: 'eyJ.dummy_token' } });
      }
      return sendJson(res, 401, { message: 'Unauthorized' });
    }

    // ----------------------------------------------------
    // EVENT
    // ----------------------------------------------------
    if (path.startsWith('/api/event') || path.startsWith('/api/events')) {
      // Create Event
      if (method === 'POST') {
        const body = await parseBody(req);
        const newEvent = { ...body, eventId: nextEventId++ };
        events.push(newEvent);
        return sendJson(res, 201, { status: 201, message: 'Created', data: newEvent });
      }
      
      // Update Event (PUT /api/event/:id)
      if (method === 'PUT') {
        const match = path.match(/\/(?:events?)\/(\d+)/);
        if (match) {
          const id = Number(match[1]);
          const body = await parseBody(req);
          const idx = events.findIndex(e => e.eventId === id);
          if (idx === -1) return sendJson(res, 404, { message: 'Not Found' });
          events[idx] = { ...events[idx], ...body };
          return sendJson(res, 200, { status: 200, message: 'Updated', data: events[idx] });
        }
      }

      // Delete Event (DELETE /api/event/:id)
      if (method === 'DELETE') {
        const match = path.match(/\/(?:events?)\/(\d+)/);
        if (match) {
          const id = Number(match[1]);
          events = events.filter(e => e.eventId !== id);
          return sendJson(res, 200, { status: 200, message: 'Deleted', data: {} });
        }
      }

      // Get Events
      if (method === 'GET') {
        return sendJson(res, 200, { data: events });
      }
    }

    // ----------------------------------------------------
    // ROOM
    // ----------------------------------------------------
    if (path === '/api/room/data' && method === 'GET') {
      return sendJson(res, 200, { data: rooms });
    }
    
    if (path === '/api/room/map' && method === 'GET') {
      return sendJson(res, 200, { data: roomMaps });
    }

    if (path === '/api/room/name' && method === 'GET') {
      return sendJson(res, 200, { data: rooms.map(r => ({ roomId: r.roomId, name: r.name })) });
    }

    if (path.match(/^\/api\/room\/\d+\/demo-action$/) && method === 'POST') {
      await parseBody(req); // Parse but ignore
      return sendJson(res, 200, { data: rooms }); // Returns rooms state after action
    }

    // ----------------------------------------------------
    // ROBOT
    // ----------------------------------------------------
    if (path === '/api/robot/status' && method === 'GET') {
      // Simulate robot movement
      robotStatus.pose.x = Math.max(0, Math.min(1, robotStatus.pose.x + (Math.random() - 0.5) * 0.05));
      robotStatus.pose.y = Math.max(0, Math.min(1, robotStatus.pose.y + (Math.random() - 0.5) * 0.05));
      robotStatus.stamp = new Date().toISOString();
      return sendJson(res, 200, { data: robotStatus });
    }

    // ----------------------------------------------------
    // SCHEDULE
    // ----------------------------------------------------
    if (path.startsWith('/api/schedule') || path.startsWith('/api/schedules')) {
      if (method === 'POST') {
        const body = await parseBody(req);
        const newSch = { ...body, scheduleId: nextScheduleId++ };
        schedules.push(newSch);
        return sendJson(res, 201, { status: 201, message: 'Created', data: newSch });
      }
      
      if (method === 'PUT') {
        const match = path.match(/\/(?:schedules?)\/(\d+)/);
        if (match) {
          const id = Number(match[1]);
          const body = await parseBody(req);
          const idx = schedules.findIndex(s => s.scheduleId === id);
          if (idx === -1) return sendJson(res, 404, { message: 'Not Found' });
          schedules[idx] = { ...schedules[idx], ...body };
          return sendJson(res, 200, { status: 200, message: 'Updated', data: schedules[idx] });
        }
      }

      if (method === 'DELETE') {
        const match = path.match(/\/(?:schedules?)\/(\d+)/);
        if (match) {
          const id = Number(match[1]);
          schedules = schedules.filter(s => s.scheduleId !== id);
          return sendJson(res, 200, { status: 200, message: 'Deleted', data: {} });
        }
      }

      if (method === 'GET') {
        return sendJson(res, 200, { data: schedules });
      }
    }

    // ----------------------------------------------------
    // NOT FOUND
    // ----------------------------------------------------
    return sendJson(res, 404, { message: 'Endpoint not found mock server' });

  } catch (err) {
    console.error(err);
    return sendJson(res, 500, { message: 'Internal Server Error' });
  }
});

server.listen(PORT, () => {
  console.log(`🚀 Dummy Full API Server running at http://localhost:${PORT}`);
  console.log(`📌 Supported mock endpoints based on api-spec:`);
  console.log(`   - Auth: POST /api/v1/auth/login`);
  console.log(`   - Event: GET/POST/PUT/DELETE /api/v1/event`);
  console.log(`   - Room: GET /api/v1/room/data, /api/v1/room/map, /api/v1/room/name`);
  console.log(`   - Robot: GET /api/v1/robot/status`);
  console.log(`   - Schedule: GET/POST/PUT/DELETE /api/v1/schedule`);
  console.log(`🔑 Test Account -> Email: admin@ssafy.com / PW: 1234`);
});
