import { Navigate, Route, Routes } from 'react-router';
import ProtectedRoute from '~/components/layout/protected-route';
import ControlPage from '~/pages/control/page';
import DashboardPage from '~/pages/dashboard/page';
import EventsPage from '~/pages/events/page';
import LoginPage from '~/pages/login/page';
import SchedulesPage from '~/pages/schedules/page';
import AppLayout from './layouts/app-layout';
import AuthLayout from './layouts/auth-layout';

export default function AppRouter() {
  return (
    <Routes>
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/control" element={<ControlPage />} />
          <Route path="/events" element={<EventsPage />} />
          <Route path="/schedules" element={<SchedulesPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
