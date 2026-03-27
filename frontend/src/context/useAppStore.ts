import { useContext } from 'react';
import type { Dispatch } from 'react';

import { AppDispatchContext, AppStateContext } from './AppContexts';
import type { AppState } from '../types';
import type { AppAction } from './appReducer';

export function useAppState(): AppState {
  const context = useContext(AppStateContext);
  if (!context) {
    throw new Error('useAppState must be used within AppProvider');
  }
  return context;
}

export function useAppDispatch(): Dispatch<AppAction> {
  const context = useContext(AppDispatchContext);
  if (!context) {
    throw new Error('useAppDispatch must be used within AppProvider');
  }
  return context;
}
