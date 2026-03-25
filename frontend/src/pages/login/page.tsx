import { useState } from 'react';
import { useNavigate } from 'react-router';
import { Button } from '~/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '~/components/ui/card';
import { Input } from '~/components/ui/input';
import { useAuthStore } from '~/store/auth-store';
import { useLoginMutation } from './api/queries';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [pw, setPw] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const loginMutation = useLoginMutation();
  const setToken = useAuthStore(state => state.setToken);
  const navigate = useNavigate();

  // 브라우저 경고(평문 전송) 방지를 위한 간단한 SHA-256 해싱
  const hashPassword = async (password: string) => {
    const msgBuffer = new TextEncoder().encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    const hashedPw = await hashPassword(pw);

    loginMutation.mutate(
      { email, pw: hashedPw },
      {
        onSuccess: (res) => {
          if (res.accessToken) {
            setToken(res.accessToken);
            navigate('/', { replace: true });
          }
          else {
            setErrorMsg('서버 응답에서 토큰을 찾을 수 없습니다.');
          }
        },
        onError: (err: any) => {
          if (err?.response?.status === 401) {
            setErrorMsg('이메일 또는 비밀번호가 잘못되었습니다.');
          }
          else if (err?.response?.status === 400) {
            setErrorMsg('입력값이 양식에 맞지 않습니다.');
          }
          else if (err?.response?.status === 500) {
            setErrorMsg('서버 내부 오류가 발생했습니다. 잠시 후 시도해주세요.');
          }
          else {
            setErrorMsg('로그인 중 알 수 없는 문제가 발생했습니다.');
          }
        },
      },
    );
  };

  return (
    <Card className="w-full mx-auto max-w-sm rounded-3xl border-none bg-surface shadow-xl">
      <CardHeader className="items-center pb-6 pt-8 text-center">
        <CardTitle className="text-2xl font-bold text-fg-strong">환영합니다</CardTitle>
        <CardDescription className="text-sm text-fg-muted">기기 제어를 위해 로그인해 주세요.</CardDescription>
      </CardHeader>

      <CardContent className="pb-8">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="pl-4 text-sm font-bold text-fg-strong" htmlFor="email">
              이메일
            </label>
            <Input
              id="email"
              type="email"
              required
              placeholder="hello@example.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="pl-4 text-sm font-bold text-fg-strong" htmlFor="password">
              비밀번호
            </label>
            <Input
              id="password"
              type="password"
              required
              placeholder="비밀번호를 입력해주세요."
              value={pw}
              onChange={e => setPw(e.target.value)}
            />
          </div>

          {errorMsg && (
            <p className="mt-2 text-center text-sm font-medium text-danger animate-in fade-in">
              {errorMsg}
            </p>
          )}

          <Button
            type="submit"
            disabled={loginMutation.isPending}
            variant="brand"
            size="xl"
            className="mt-4 w-full"
          >
            {loginMutation.isPending ? '로그인 중...' : '로그인'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
