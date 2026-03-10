import type React from 'react';
import { useState } from 'react';
import { ApiErrorAlert } from '../components/common';
import { useNavigate, useSearchParams } from 'react-router-dom';
import type { ParsedApiError } from '../api/error';
import { isParsedApiError } from '../api/error';
import { useAuth } from '../hooks';
import { SettingsAlert } from '../components/settings';

const LoginPage: React.FC = () => {
  const { login, passwordSet } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const rawRedirect = searchParams.get('redirect') ?? '';
  const redirect =
    rawRedirect.startsWith('/') && !rawRedirect.startsWith('//') ? rawRedirect : '/';

  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | ParsedApiError | null>(null);

  const isFirstTime = !passwordSet;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (isFirstTime && password !== passwordConfirm) {
      setError('兩次輸入的密碼不一致');
      return;
    }
    setIsSubmitting(true);
    try {
      const result = await login(password, isFirstTime ? passwordConfirm : undefined);
      if (result.success) {
        navigate(redirect, { replace: true });
      } else {
        setError(result.error ?? '登入失敗');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-base px-4">
      <div className="w-full max-w-sm rounded-2xl border border-white/8 bg-card/80 p-6 backdrop-blur-sm">
        <h1 className="mb-2 text-xl font-semibold text-white">
          {isFirstTime ? '設定初始密碼' : '管理員登入'}
        </h1>
        <p className="mb-6 text-sm text-secondary">
          {isFirstTime
            ? '請設定管理員密碼，輸入兩遍確認'
            : '請輸入密碼以繼續訪問'}
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="password" className="mb-1 block text-sm font-medium text-secondary">
              {isFirstTime ? '新密碼' : '密碼'}
            </label>
            <input
              id="password"
              type="password"
              className="input-terminal"
              placeholder={isFirstTime ? '輸入新密碼' : '輸入密碼'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isSubmitting}
              autoFocus
              autoComplete={isFirstTime ? 'new-password' : 'current-password'}
            />
          </div>

          {isFirstTime ? (
            <div>
              <label
                htmlFor="passwordConfirm"
                className="mb-1 block text-sm font-medium text-secondary"
              >
                確認密碼
              </label>
              <input
                id="passwordConfirm"
                type="password"
                className="input-terminal"
                placeholder="再次輸入密碼"
                value={passwordConfirm}
                onChange={(e) => setPasswordConfirm(e.target.value)}
                disabled={isSubmitting}
                autoComplete="new-password"
              />
            </div>
          ) : null}

          {error
            ? isParsedApiError(error)
              ? <ApiErrorAlert error={error} className="!mt-3" />
              : (
                <SettingsAlert
                  title={isFirstTime ? '設定失敗' : '登入失敗'}
                  message={error}
                  variant="error"
                  className="!mt-3"
                />
              )
            : null}

          <button
            type="submit"
            className="btn-primary w-full"
            disabled={isSubmitting}
          >
            {isSubmitting ? (isFirstTime ? '設定中...' : '登入中...') : isFirstTime ? '設定密碼' : '登入'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
