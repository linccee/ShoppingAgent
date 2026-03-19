import { useMemo, useReducer } from 'react';
import type { PropsWithChildren } from 'react';

import { appReducer, initialAppState } from './appReducer';
import { AppDispatchContext, AppStateContext } from './AppContexts';

export function AppProvider({ children }: PropsWithChildren) {
  const [state, dispatch] = useReducer(appReducer, initialAppState);
  const stateValue = useMemo(() => state, [state]);

  return (
    <AppDispatchContext.Provider value={dispatch}>
      <AppStateContext.Provider value={stateValue}>{children}</AppStateContext.Provider>
    </AppDispatchContext.Provider>
  );
}
