import { create } from 'zustand';

export interface DemoModule {
  moduleId: number;
  type: string;
  status: string;
}

const DEMO_MODULES: DemoModule[] = [
  { moduleId: 1, type: 'AIR_PURIFIER',  status: 'IDLE' },
  { moduleId: 2, type: 'HUMIDIFIER',    status: 'IDLE' },
  { moduleId: 3, type: 'DEHUMIDIFIER',  status: 'IDLE' },
  { moduleId: 4, type: 'STERILIZER',    status: 'IDLE' },
  { moduleId: 5, type: 'DIFFUSER',      status: 'IDLE' },
];

interface DemoStore {
  /** undefined = 미설정(API 데이터 사용), null = 모듈 없음, DemoModule = 가짜 모듈 */
  fakeModule: DemoModule | null | undefined;
  setFakeModule: (index: number) => void; // 0 = 없음, 1~5 = 모듈
}

export const useDemoStore = create<DemoStore>((set) => ({
  fakeModule: undefined,
  setFakeModule: (index) =>
    set({ fakeModule: index === 0 ? null : (DEMO_MODULES[index - 1] ?? null) }),
}));
