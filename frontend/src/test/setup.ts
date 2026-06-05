import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import i18n from 'i18next';
import { afterEach } from 'vitest';
import { initReactI18next } from 'react-i18next';

import chat from '../../public/locales/zh-CN/chat.json';
import common from '../../public/locales/zh-CN/common.json';
import profile from '../../public/locales/zh-CN/profile.json';
import sidebar from '../../public/locales/zh-CN/sidebar.json';

afterEach(() => {
  cleanup();
});

await i18n.use(initReactI18next).init({
  lng: 'zh-CN',
  fallbackLng: 'zh-CN',
  ns: ['common', 'chat', 'profile', 'sidebar'],
  defaultNS: 'common',
  resources: {
    'zh-CN': {
      common,
      chat,
      profile,
      sidebar,
    },
  },
  interpolation: {
    escapeValue: false,
  },
  react: {
    useSuspense: false,
  },
});
