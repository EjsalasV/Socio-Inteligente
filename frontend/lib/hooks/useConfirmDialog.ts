import { useState } from 'react';

export interface ConfirmDialogState {
  isOpen: boolean;
  title: string;
  message: string;
  actionLabel: string;
  isDangerous: boolean;
  isLoading: boolean;
  resolve?: (confirmed: boolean) => void;
}

export function useConfirmDialog() {
  const [state, setState] = useState<ConfirmDialogState>({
    isOpen: false,
    title: '',
    message: '',
    actionLabel: 'Confirmar',
    isDangerous: false,
    isLoading: false,
  });

  const confirm = (options: {
    title: string;
    message: string;
    actionLabel?: string;
    isDangerous?: boolean;
  }): Promise<boolean> => {
    return new Promise((resolve) => {
      setState({
        isOpen: true,
        title: options.title,
        message: options.message,
        actionLabel: options.actionLabel || 'Confirmar',
        isDangerous: options.isDangerous || false,
        isLoading: false,
        resolve,
      });
    });
  };

  const handleConfirm = () => {
    if (state.resolve) {
      state.resolve(true);
    }
    setState((prev) => ({ ...prev, isOpen: false }));
  };

  const handleCancel = () => {
    if (state.resolve) {
      state.resolve(false);
    }
    setState((prev) => ({ ...prev, isOpen: false }));
  };

  const setLoading = (isLoading: boolean) => {
    setState((prev) => ({ ...prev, isLoading }));
  };

  return {
    state,
    confirm,
    handleConfirm,
    handleCancel,
    setLoading,
  };
}
