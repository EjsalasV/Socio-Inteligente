'use client';

import { useEffect, useState } from 'react';

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

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isOpen) {
      setInputValue('');
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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onCancel}
        aria-hidden="true"
      />

      <div className="relative z-10 w-full max-w-md rounded-lg bg-white shadow-2xl">
        <div className="border-b border-gray-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
        </div>

        <div className="px-6 py-4">
          <p className="mb-4 whitespace-pre-wrap text-sm text-gray-700">
            {message}
          </p>

          {isDangerous && (
            <div className="mb-4 rounded-lg bg-red-50 p-4">
              <p className="mb-2 text-xs font-semibold text-red-900">
                Esta accion no se puede deshacer.
              </p>
              <p className="mb-3 text-xs text-red-800">
                Escribe "CONFIRMAR" para continuar:
              </p>
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Escribe CONFIRMAR"
                className="w-full rounded border border-red-300 px-3 py-2 text-sm text-gray-900 placeholder-gray-500 focus:border-red-500 focus:outline-none focus:ring-2 focus:ring-red-200"
                autoFocus
                disabled={isLoading}
              />
            </div>
          )}
        </div>

        <div className="flex gap-3 border-t border-gray-200 px-6 py-4">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="flex-1 rounded border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            disabled={isConfirmDisabled}
            className={`flex-1 rounded px-4 py-2 text-sm font-medium text-white transition-colors ${
              isDangerous
                ? 'bg-red-600 hover:bg-red-700 disabled:bg-red-300'
                : 'bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300'
            } disabled:cursor-not-allowed`}
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

        <div className="border-t border-gray-200 bg-gray-50 px-6 py-3">
          <p className="text-xs text-gray-500">
            {isDangerous ? 'Presiona ESC para cancelar' : 'Presiona ESC para cancelar'}
          </p>
        </div>
      </div>
    </div>
  );
}
