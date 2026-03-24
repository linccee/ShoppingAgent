import { Navigate, Outlet } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';

export default function PrivateRoute() {
  const { isAuthenticated, isLoading } = useAuth();
  const { t } = useTranslation('common');

  if (isLoading) {
    return <div>{t('privateRouteLoading')}</div>;
  }

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}
