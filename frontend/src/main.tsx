import React, { Suspense } from 'react';
import ReactDOM from 'react-dom/client';

import './i18n';
import './styles/global.css';

import App from './App';
import { Loading } from './components/common/Loading';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Suspense fallback={<Loading />}>
      <App />
    </Suspense>
  </React.StrictMode>,
);
