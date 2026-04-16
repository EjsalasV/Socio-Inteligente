'use client';

import { useMemo } from 'react';
import { useRealtimeSync, RealtimeParticipant } from '@/lib/hooks/useRealtimeSync';

interface OnlineStatusProps {
  clienteId: string;
  userId?: string;
  module?: string;
}

export function OnlineStatus({
  clienteId,
  userId,
  module = 'general',
}: OnlineStatusProps) {
  const { isConnected, participants } = useRealtimeSync({
    clienteId,
    module,
  });

  const otherUsers = useMemo(
    () =>
      participants.filter((p) => userId ? p.user_id !== userId : true) || [],
    [participants, userId]
  );

  const activeCount = otherUsers.length;

  if (!isConnected) {
    return (
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <span className="inline-block h-2 w-2 rounded-full bg-gray-400" />
        Desconectado
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2 text-xs">
        <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-green-500" />
        <span className="text-gray-600">
          {activeCount === 0
            ? 'Solo tu'
            : `${activeCount} usuario${activeCount !== 1 ? 's' : ''} en linea`}
        </span>
      </div>

      {activeCount > 0 && (
        <div className="rounded-lg bg-blue-50 p-2">
          <div className="mb-1 text-xs font-semibold text-gray-700">
            Usuarios activos:
          </div>
          <div className="space-y-1">
            {otherUsers.map((participant) => (
              <div key={participant.user_id} className="flex items-center justify-between rounded px-2 py-1 text-xs">
                <div className="flex items-center gap-2">
                  <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
                  <span className="font-medium text-gray-700">
                    {participant.display_name}
                  </span>
                </div>
                <span className="rounded bg-green-100 px-1.5 py-0.5 text-xs font-semibold text-green-800">
                  {participant.role}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
