import { Navigate, Route, Routes } from 'react-router';
import DashboardPage from '~/pages/dashboard/page';
import AppLayout from './layouts/app-layout';
import AuthLayout from './layouts/auth-layout';

export default function AppRouter() {
  return (
    <Routes>
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<DashboardPage />} />
      </Route>

      <Route element={<AppLayout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/control" element={<DashboardPage />} />
        <Route path="/events" element={<DashboardPage />} />
        <Route path="/schedules" element={<DashboardPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
