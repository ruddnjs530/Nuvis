/**
 * snake_case 키를 camelCase로 재귀 변환하는 유틸
 * AI 서버 응답을 프론트엔드에 반환할 때 사용합니다.
 */
export function toCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
}

export function keysToCamel(obj: unknown): unknown {
  if (Array.isArray(obj)) {
    return obj.map(keysToCamel);
  }
  if (obj !== null && typeof obj === 'object') {
    return Object.fromEntries(
      Object.entries(obj as Record<string, unknown>).map(([k, v]) => [
        toCamel(k),
        keysToCamel(v),
      ]),
    );
  }
  return obj;
}
