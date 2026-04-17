'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CartaControl } from '@/components/reportes/CartaControl';

export default function ReportesPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const clienteId = searchParams.get('cliente_id');
  const clienteNombre = searchParams.get('cliente_nombre');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(false);
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="mb-4">Cargando...</div>
        </div>
      </div>
    );
  }

  if (!clienteId) {
    return (
      <div className="p-6">
        <div className="border border-red-300 bg-red-50 text-red-800 p-4 rounded">
          <div className="font-semibold">Error</div>
          <div>No se especificó cliente. Por favor selecciona un cliente desde el dashboard.</div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <CartaControl
        clienteId={clienteId}
        clienteNombre={clienteNombre || 'Cliente'}
      />
    </div>
  );
}
