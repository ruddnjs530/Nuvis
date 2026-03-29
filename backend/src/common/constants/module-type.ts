export const MODULE_TYPE_TO_ID: Record<string, number> = {
  NONE: 0,
  AIR_PURIFIER: 1,
  HUMIDIFIER: 2,
  DEHUMIDIFIER: 3,
  STERILIZER: 4,
  DIFFUSER: 5,
};

export const MODULE_ID_TO_TYPE: Record<number, string> = {
  0: 'NONE',
  1: 'AIR_PURIFIER',
  2: 'HUMIDIFIER',
  3: 'DEHUMIDIFIER',
  4: 'STERILIZER',
  5: 'DIFFUSER',
};
