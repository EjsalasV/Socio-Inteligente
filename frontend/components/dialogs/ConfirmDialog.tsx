'use client';

import { useEffect, useState, useRef } from 'react';

export interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  actionLabel?: string;
  isDangerous?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function ConfirmDialog({
  isOpen,
  title,
  message,
  actionLabel = 'Confirmar',
  isDangerous = false,
  onConfirm,
  onCancel,
  isLoading = false,
}: ConfirmDialogProps) {
  const [inputValue, setInputValue] = useState('');
  const [isMounted, setIsMounted] = useState(false);
  const dialogRef = useRef<HTMLDivElement>(null);
  const titleId = 'confirm-dialog-title';
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isOpen) {
      setInputValue('');
      // Restore previous focus when dialog closes
      if (previousFocusRef.current) {
        previousFocusRef.current.focus();
      }
    } else {
      // Store previous focus when dialog opens
      previousFocusRef.current = document.activeElement as HTMLElement;
      // Focus first interactive element in dialog
      setTimeout(() => {
        const confirmBtn = dialogRef.current?.querySelector('input, [type="button"]:not([disabled])') as HTMLElement;
        if (confirmBtn) {
          confirmBtn.focus();
        }
      }, 0);
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen || !isMounted) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCancel();
      }
      if (e.key === 'Enter' && !isDangerous) {
        if (!isLoading) {
          onConfirm();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isDangerous, isLoading, onConfirm, onCancel, isMounted]);

  if (!isOpen || !isMounted) return null;

  const isConfirmDisabled = isDangerous
    ? inputValue !== 'CONFIRMAR' || isLoading
    : isLoading;

  if (!isOpen || !isMounted) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="presentation"
    >
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onCancel}
        aria-hidden="true"
      />

      <div
        ref={dialogRef}
        role="alertdialog"
        aria-labelledby={titleId}
        aria-modal="true"
        className="relative z-10 w-full max-w-md rounded-lg bg-white shadow-2xl"
      >
        <div className="border-b border-gray-200 px-6 py-4">
          <h2 id={titleId} className="text-lg font-semibold text-gray-900">
            {title}
          </h2>
        </div>

        <div className="px-6 py-4">
          <p className="mb-4 whitespace-pre-wrap text-sm text-gray-700">
            {message}
          </p>

          {isDangerous && (
            <div className="mb-4 rounded-lg bg-red-50 p-4 border border-red-200">
              <p className="mb-2 text-xs font-semibold text-red-900">
                Esta acción no se puede deshacer.
              </p>
              <label htmlFor="confirm-input" className="mb-3 block text-xs text-red-800">
                Escribe "CONFIRMAR" para continuar:
              </label>
              <input
                id="confirm-input"
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Escribe CONFIRMAR"
                className="w-full rounded border border-red-300 px-3 py-2 text-sm text-gray-900 placeholder-gray-500 focus:border-red-500 focus:outline-none focus:ring-2 focus:ring-red-200 min-h-[44px]"
                autoFocus
                disabled={isLoading}
                aria-describedby="danger-warning"
              />
            </div>
          )}
        </div>

        <div className="flex gap-3 border-t border-gray-200 px-6 py-4">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="flex-1 rounded border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400 disabled:cursor-not-allowed disabled:opacity-50 min-h-[44px]"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            disabled={isConfirmDisabled}
            className={`flex-1 rounded px-4 py-2 text-sm font-medium text-white transition-colors focus:outline-none focus:ring-2 ${
              isDangerous
                ? 'bg-red-600 hover:bg-red-700 focus:ring-red-400 disabled:bg-red-300'
                : 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-400 disabled:bg-blue-300'
            } disabled:cursor-not-allowed min-h-[44px]`}
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                Procesando...
              </span>
            ) : (
              actionLabel
            )}
          </button>
        </div>

        <div id="danger-warning" className="border-t border-gray-200 bg-gray-50 px-6 py-3">
          <p className="text-xs text-gray-500">
            Presiona ESC para cancelar
          </p>
        </div>
      </div>
    </div>
  );
}
