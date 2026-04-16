"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { CheckCircleIcon, ClockIcon, PencilIcon } from "lucide-react";

interface Signature {
  signed: boolean;
  signed_at: string | null;
  signed_by: string | null;
}

interface FirmasPanelProps {
  fileId: number;
  clienteId: string;
  areaCode: string;
  role: "junior" | "semi" | "senior" | "socio";
  signatures?: {
    junior: Signature;
    senior: Signature;
    socio: Signature;
  };
  onSignSuccess?: (role: string) => void;
}

export function FirmasPanel({
  fileId,
  clienteId,
  areaCode,
  role,
  signatures = {
    junior: { signed: false, signed_at: null, signed_by: null },
    senior: { signed: false, signed_at: null, signed_by: null },
    socio: { signed: false, signed_at: null, signed_by: null },
  },
  onSignSuccess,
}: FirmasPanelProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [signStatus, setSignStatus] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const canSign = role === "junior" || role === "semi" || role === "senior" || role === "socio";

  const getRoleLabel = (roleKey: string) => {
    const labels: Record<string, string> = {
      junior: "Completado por Junior",
      senior: "Revisado por Senior",
      socio: "Finalizado por Socio",
    };
    return labels[roleKey] || roleKey;
  };

  const getRoleDescription = (roleKey: string) => {
    const descriptions: Record<string, string> = {
      junior: "Indica que el Junior ha ejecutado y completado el trabajo",
      senior: "Indica que el Senior ha revisado y validado la calidad",
      socio: "Indica que el Socio ha aprobado y finalizado el documento",
    };
    return descriptions[roleKey] || "";
  };

  const formatTimestamp = (timestamp: string | null) => {
    if (!timestamp) return "No firmado";
    const date = new Date(timestamp);
    return date.toLocaleString("es-ES", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const handleSign = async (signRole: string) => {
    // Validate permissions
    if (role === "junior" && signRole !== "junior") {
      setSignStatus({
        type: "error",
        message: "Junior solo puede firmar como Junior",
      });
      return;
    }
    if (role === "semi" && signRole !== "junior") {
      setSignStatus({
        type: "error",
        message: "Semi solo puede firmar como Junior",
      });
      return;
    }
    if (role === "senior" && signRole !== "senior") {
      setSignStatus({
        type: "error",
        message: "Senior solo puede firmar como Senior",
      });
      return;
    }
    if (role === "socio" && signRole !== "socio") {
      setSignStatus({
        type: "error",
        message: "Socio solo puede firmar como Socio",
      });
      return;
    }

    try {
      setIsLoading(true);
      const response = await fetch(
        `/api/papeles-trabajo/${clienteId}/${areaCode}/${fileId}/sign`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ role: signRole }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.message || `Error: ${response.statusText}`
        );
      }

      const data = await response.json();

      setSignStatus({
        type: "success",
        message: `Firmado correctamente como ${signRole.toUpperCase()}`,
      });

      if (onSignSuccess) {
        onSignSuccess(signRole);
      }

      // Reset status after 3 seconds
      setTimeout(() => setSignStatus(null), 3000);
    } catch (error) {
      setSignStatus({
        type: "error",
        message: `Error al firmar: ${error instanceof Error ? error.message : "Error desconocido"}`,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const allSigned =
    signatures.junior.signed &&
    signatures.senior.signed &&
    signatures.socio.signed;

  return (
    <div className="w-full max-w-4xl mx-auto p-6 bg-white rounded-lg shadow">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Panel de Firmas
        </h2>
        <div className="flex items-center gap-3">
          <div className="h-3 w-3 rounded-full bg-gray-300"></div>
          <p className="text-gray-600">
            Estado: {allSigned ? "✅ COMPLETADO" : "⏳ PENDIENTE"}
          </p>
        </div>
      </div>

      {/* Signatures Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {Object.entries(signatures).map(([signRole, signature]) => (
          <div
            key={signRole}
            className={`border-2 rounded-lg p-5 transition-all ${
              signature.signed
                ? "border-green-300 bg-green-50"
                : "border-gray-300 bg-gray-50"
            }`}
          >
            {/* Role Title */}
            <div className="flex items-center gap-2 mb-3">
              {signature.signed ? (
                <CheckCircleIcon size={24} className="text-green-600" />
              ) : (
                <ClockIcon size={24} className="text-gray-400" />
              )}
              <div>
                <h3 className="font-bold text-gray-900 capitalize">
                  {getRoleLabel(signRole)}
                </h3>
                <p className="text-xs text-gray-600 mt-0.5">
                  {getRoleDescription(signRole)}
                </p>
              </div>
            </div>

            {/* Timestamp and Signer */}
            <div className="space-y-2 mb-4">
              <div>
                <p className="text-xs font-semibold text-gray-700 uppercase">Fecha/Hora</p>
                <p
                  className={`text-sm ${
                    signature.signed ? "text-gray-900 font-mono" : "text-gray-500"
                  }`}
                >
                  {formatTimestamp(signature.signed_at)}
                </p>
              </div>
              {signature.signed && signature.signed_by && (
                <div>
                  <p className="text-xs font-semibold text-gray-700 uppercase">Firmado por</p>
                  <p className="text-sm text-gray-900 font-medium">{signature.signed_by}</p>
                </div>
              )}
            </div>

            {/* Sign Button */}
            {!signature.signed && canSign && (
              <Button
                onClick={() => handleSign(signRole)}
                disabled={isLoading || role !== signRole}
                className={`w-full mt-3 flex items-center justify-center gap-2 ${
                  role === signRole
                    ? "bg-blue-600 hover:bg-blue-700 text-white"
                    : "bg-gray-300 text-gray-600 cursor-not-allowed"
                }`}
              >
                <PencilIcon size={16} />
                {role === signRole ? `Firmar como ${signRole.toUpperCase()}` : `No tienes permisos`}
              </Button>
            )}

            {signature.signed && (
              <div className="w-full mt-3 py-2 text-center bg-green-100 rounded border border-green-200 text-green-700 font-semibold text-sm">
                ✓ Firmado
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Status Message */}
      {signStatus && (
        <div
          className={`p-4 rounded-lg mb-6 ${
            signStatus.type === "success"
              ? "bg-green-50 border border-green-200 text-green-900"
              : "bg-red-50 border border-red-200 text-red-900"
          }`}
        >
          <p className="font-medium">{signStatus.message}</p>
        </div>
      )}

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
        <p className="text-sm text-blue-900">
          <span className="font-semibold">ℹ️ Proceso de firmas:</span> Los papeles de trabajo deben ser
          firmados por Junior (Completado), Senior (Revisado) y Socio (Finalizado) en ese orden.
          Cada firma registra quién firmó y cuándo.
        </p>
      </div>

      {/* Role-specific info */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <p className="text-sm text-gray-700">
          <span className="font-semibold">Tu rol actual:</span> <span className="capitalize font-mono">{role}</span>
        </p>
        <p className="text-xs text-gray-600 mt-2">
          {role === "junior" && "Puedes firmar como Junior para indicar que completaste el trabajo."}
          {role === "semi" && "Puedes firmar como Junior para indicar que completaste el trabajo."}
          {role === "senior" && "Puedes firmar como Senior para indicar que revisaste y validaste."}
          {role === "socio" && "Puedes firmar como Socio para indicar aprobación final."}
        </p>
      </div>
    </div>
  );
}
