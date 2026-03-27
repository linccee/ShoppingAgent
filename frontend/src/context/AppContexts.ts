import { createContext } from 'react';
import type { Dispatch } from 'react';

import type { AppAction } from './appReducer';
import type { AppState } from '../types';

export const AppStateContext = createContext<AppState | undefined>(undefined);
export const AppDispatchContext = createContext<Dispatch<AppAction> | undefined>(undefined);
