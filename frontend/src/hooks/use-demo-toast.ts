import { useEffect } from 'react';
import { useDemoStore } from '~/store/demo-store';
import { useToastStore } from '~/store/toast-store';

/**
 * 데모 시연용 키 이벤트 훅.
 * T 키를 누르면 미세먼지 경고 토스트를 출력합니다.
 */
export function useDemoToast() {
  const add = useToastStore(s => s.add);
  const setFakeModule = useDemoStore(s => s.setFakeModule);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      // input/textarea에 포커스 중이면 무시
      const tag = (e.target as HTMLElement).tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA')
        return;

      if (e.key === 't' || e.key === 'T') {
        add('침실 2의 미세먼지 농도가 높아 공기청정기를 가동합니다.', 'info');
      }

      const digit = Number(e.key);
      if (!Number.isNaN(digit) && digit >= 0 && digit <= 5) {
        setFakeModule(digit);
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [add, setFakeModule]);
}
