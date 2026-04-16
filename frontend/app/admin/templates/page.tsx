'use client';

import { useState, useEffect } from 'react';
import { useAuditContext } from '@/lib/hooks/useAuditContext';

interface ReportTemplate {
  id: string;
  cliente_id: string;
  nombre: string;
  descripcion?: string;
  report_type: string;
  estructura: Record<string, any>;
  activo: boolean;
  created_at: string;
  updated_at: string;
}

export default function TemplatesPage() {
  const { clienteId } = useAuditContext();
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showDialog, setShowDialog] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    nombre: '',
    descripcion: '',
    report_type: 'resumen',
    estructura: '{"template": "<h2>{{ cliente_nombre }}</h2>"}',
  });

  const loadTemplates = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/templates/${clienteId || 'default'}`, {
        headers: { 'Content-Type': 'application/json' },
      });
      if (response.ok) {
        const data = await response.json();
        setTemplates(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      console.error('Error loading templates:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTemplates();
  }, [clienteId]);

  const handleSave = async () => {
    if (!formData.nombre.trim()) {
      alert('El nombre del template es requerido');
      return;
    }

    try {
      let estructura;
      try {
        estructura = JSON.parse(formData.estructura);
      } catch {
        estructura = { template: formData.estructura };
      }

      const payload = {
        nombre: formData.nombre,
        descripcion: formData.descripcion,
        report_type: formData.report_type,
        estructura,
      };

      const url = editingId
        ? `/api/templates/${clienteId}/${editingId}`
        : `/api/templates/${clienteId}`;
      const method = editingId ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        setShowDialog(false);
        setFormData({
          nombre: '',
          descripcion: '',
          report_type: 'resumen',
          estructura: '{"template": ""}',
        });
        setEditingId(null);
        await loadTemplates();
      }
    } catch (error) {
      console.error('Error saving template:', error);
    }
  };

  const handleDelete = async (templateId: string) => {
    if (!confirm('¿Está seguro que desea eliminar este template?')) {
      return;
    }

    try {
      const response = await fetch(`/api/templates/${clienteId}/${templateId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        await loadTemplates();
      }
    } catch (error) {
      console.error('Error deleting template:', error);
    }
  };

  const handleEdit = (template: ReportTemplate) => {
    setEditingId(template.id);
    setFormData({
      nombre: template.nombre,
      descripcion: template.descripcion || '',
      report_type: template.report_type,
      estructura: JSON.stringify(template.estructura, null, 2),
    });
    setShowDialog(true);
  };

  return (
    <main className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-navy-900">Templates de Reportes</h1>
        <button
          onClick={() => {
            setEditingId(null);
            setFormData({
              nombre: '',
              descripcion: '',
              report_type: 'resumen',
              estructura: '{"template": ""}',
            });
            setShowDialog(true);
          }}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
          aria-label="Crear nuevo template"
        >
          Nuevo Template
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-8">Cargando templates...</div>
      ) : templates.length === 0 ? (
        <div className="text-center py-8 text-slate-500">
          No hay templates disponibles. Crea uno nuevo.
        </div>
      ) : (
        <div className="grid gap-4">
          {templates.map((template) => (
            <div
              key={template.id}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h3 className="font-semibold text-gray-900">{template.nombre}</h3>
                  <p className="text-sm text-gray-600">{template.descripcion}</p>
                  <span className="inline-block mt-2 px-2 py-1 text-xs bg-gray-100 rounded">
                    {template.report_type}
                  </span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(template)}
                    className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-400 min-h-[44px]"
                    aria-label={`Editar template ${template.nombre}`}
                  >
                    Editar
                  </button>
                  <button
                    onClick={() => handleDelete(template.id)}
                    className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-400 min-h-[44px]"
                    aria-label={`Eliminar template ${template.nombre}`}
                  >
                    Eliminar
                  </button>
                </div>
              </div>
            </div>
          ))}
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
                {editingId ? 'Editar Template' : 'Nuevo Template'}
              </h2>
            </div>

            <div className="px-6 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre
                </label>
                <input
                  type="text"
                  value={formData.nombre}
                  onChange={(e) =>
                    setFormData({ ...formData, nombre: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
                  placeholder="Nombre del template"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Descripción
                </label>
                <input
                  type="text"
                  value={formData.descripcion}
                  onChange={(e) =>
                    setFormData({ ...formData, descripcion: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
                  placeholder="Descripción opcional"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo de Reporte
                </label>
                <select
                  value={formData.report_type}
                  onChange={(e) =>
                    setFormData({ ...formData, report_type: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
                >
                  <option value="resumen">Resumen</option>
                  <option value="completo">Completo</option>
                  <option value="hallazgos">Hallazgos</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  HTML/Jinja2 Template
                </label>
                <textarea
                  value={formData.estructura}
                  onChange={(e) =>
                    setFormData({ ...formData, estructura: e.target.value })
                  }
                  rows={10}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  placeholder='{"template": "<h2>{{ cliente_nombre }}</h2>"}'
                />
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
