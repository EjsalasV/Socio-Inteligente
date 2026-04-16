'use client';

import { useState, useEffect } from 'react';
import { useAuditContext } from '@/lib/hooks/useAuditContext';

interface Webhook {
  id: string;
  cliente_id: string;
  evento: string;
  url: string;
  headers?: Record<string, string>;
  activo: boolean;
  created_at: string;
  updated_at: string;
}

export default function WebhooksPage() {
  const { clienteId } = useAuditContext();
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showDialog, setShowDialog] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<any>(null);
  const [formData, setFormData] = useState({
    evento: 'hallazgo_creado',
    url: '',
    headers: '{}',
    activo: true,
  });

  const eventos = [
    'hallazgo_creado',
    'alert_critico',
    'reporte_emitido',
    'gate_fallido',
  ];

  const loadWebhooks = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/webhooks/${clienteId || 'default'}`, {
        headers: { 'Content-Type': 'application/json' },
      });
      if (response.ok) {
        const data = await response.json();
        setWebhooks(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      console.error('Error loading webhooks:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadWebhooks();
  }, [clienteId]);

  const handleSave = async () => {
    if (!formData.url.trim()) {
      alert('La URL del webhook es requerida');
      return;
    }

    try {
      let headers: Record<string, string> = {};
      try {
        headers = JSON.parse(formData.headers);
      } catch {
        // Use empty headers if invalid JSON
      }

      const payload = {
        evento: formData.evento,
        url: formData.url,
        headers,
        activo: formData.activo,
      };

      const url = editingId
        ? `/api/webhooks/${clienteId}/${editingId}`
        : `/api/webhooks/${clienteId}`;
      const method = editingId ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        setShowDialog(false);
        setFormData({
          evento: 'hallazgo_creado',
          url: '',
          headers: '{}',
          activo: true,
        });
        setEditingId(null);
        await loadWebhooks();
      }
    } catch (error) {
      console.error('Error saving webhook:', error);
    }
  };

  const handleTest = async (webhookId: string) => {
    try {
      const response = await fetch(
        `/api/webhooks/${clienteId}/${webhookId}/test`,
        { method: 'POST' }
      );
      if (response.ok) {
        const data = await response.json();
        setTestResult(data);
      }
    } catch (error) {
      console.error('Error testing webhook:', error);
      setTestResult({ error: 'Error al probar webhook' });
    }
  };

  const handleDelete = async (webhookId: string) => {
    if (!confirm('¿Está seguro que desea eliminar este webhook?')) {
      return;
    }

    try {
      const response = await fetch(
        `/api/webhooks/${clienteId}/${webhookId}`,
        { method: 'DELETE' }
      );

      if (response.ok) {
        await loadWebhooks();
      }
    } catch (error) {
      console.error('Error deleting webhook:', error);
    }
  };

  const handleEdit = (webhook: Webhook) => {
    setEditingId(webhook.id);
    setFormData({
      evento: webhook.evento,
      url: webhook.url,
      headers: JSON.stringify(webhook.headers || {}, null, 2),
      activo: webhook.activo,
    });
    setShowDialog(true);
  };

  return (
    <main className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-navy-900">Webhooks</h1>
        <button
          onClick={() => {
            setEditingId(null);
            setFormData({
              evento: 'hallazgo_creado',
              url: '',
              headers: '{}',
              activo: true,
            });
            setShowDialog(true);
          }}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
          aria-label="Crear nuevo webhook"
        >
          Nuevo Webhook
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-8">Cargando webhooks...</div>
      ) : webhooks.length === 0 ? (
        <div className="text-center py-8 text-slate-500">
          No hay webhooks configurados. Crea uno nuevo.
        </div>
      ) : (
        <div className="space-y-4">
          {webhooks.map((webhook) => (
            <div
              key={webhook.id}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-gray-900">
                      {webhook.evento}
                    </h3>
                    <span
                      className={`px-2 py-1 text-xs rounded ${
                        webhook.activo
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {webhook.activo ? 'Activo' : 'Inactivo'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 break-all">{webhook.url}</p>
                </div>
                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => handleTest(webhook.id)}
                    className="px-3 py-1 text-sm bg-amber-100 text-amber-700 rounded hover:bg-amber-200 focus:outline-none focus:ring-2 focus:ring-amber-400 min-h-[44px]"
                    aria-label={`Probar webhook ${webhook.evento}`}
                  >
                    Test
                  </button>
                  <button
                    onClick={() => handleEdit(webhook)}
                    className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-400 min-h-[44px]"
                    aria-label={`Editar webhook ${webhook.evento}`}
                  >
                    Editar
                  </button>
                  <button
                    onClick={() => handleDelete(webhook.id)}
                    className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-400 min-h-[44px]"
                    aria-label={`Eliminar webhook ${webhook.evento}`}
                  >
                    Eliminar
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {testResult && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="border-b border-gray-200 px-6 py-4">
              <h3 className="font-semibold text-gray-900">Resultado de Test</h3>
            </div>
            <div className="px-6 py-4">
              <div
                className={`p-3 rounded-lg mb-3 ${
                  testResult.success
                    ? 'bg-green-50 text-green-900'
                    : 'bg-red-50 text-red-900'
                }`}
              >
                <p className="font-medium">
                  {testResult.success ? 'Éxito' : 'Error'}
                </p>
                <p className="text-sm">
                  Status: {testResult.status_code}
                </p>
                {testResult.error && (
                  <p className="text-sm">Error: {testResult.error}</p>
                )}
              </div>
            </div>
            <div className="border-t border-gray-200 px-6 py-4">
              <button
                onClick={() => setTestResult(null)}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}

      {showDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setShowDialog(false)}
            aria-hidden="true"
          />
          <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 border-b border-gray-200 px-6 py-4 bg-white">
              <h2 className="text-lg font-semibold text-gray-900">
                {editingId ? 'Editar Webhook' : 'Nuevo Webhook'}
              </h2>
            </div>

            <div className="px-6 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Evento
                </label>
                <select
                  value={formData.evento}
                  onChange={(e) =>
                    setFormData({ ...formData, evento: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
                >
                  {eventos.map((evento) => (
                    <option key={evento} value={evento}>
                      {evento}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  URL
                </label>
                <input
                  type="url"
                  value={formData.url}
                  onChange={(e) =>
                    setFormData({ ...formData, url: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
                  placeholder="https://example.com/webhook"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Headers (JSON)
                </label>
                <textarea
                  value={formData.headers}
                  onChange={(e) =>
                    setFormData({ ...formData, headers: e.target.value })
                  }
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  placeholder='{"Authorization": "Bearer token"}'
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="activo"
                  checked={formData.activo}
                  onChange={(e) =>
                    setFormData({ ...formData, activo: e.target.checked })
                  }
                  className="w-4 h-4 focus:ring-2 focus:ring-blue-500"
                />
                <label
                  htmlFor="activo"
                  className="text-sm font-medium text-gray-700"
                >
                  Activo
                </label>
              </div>
            </div>

            <div className="border-t border-gray-200 px-6 py-4 bg-gray-50 flex gap-3">
              <button
                onClick={() => setShowDialog(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400 min-h-[44px]"
              >
                Cancelar
              </button>
              <button
                onClick={handleSave}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
              >
                Guardar
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
