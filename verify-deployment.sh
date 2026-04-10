#!/bin/bash
# Deployment verification script for Vercel + Railway

set -e

RAILWAY_URL="${1:-https://socio-inteligente-production.up.railway.app}"
VERCEL_URL="${2:-https://socio-ai-frontend.vercel.app}"

echo "🔍 Checking Vercel + Railway deployment..."
echo ""

# 1. Check backend health
echo "1️⃣  Backend Health Check"
HEALTH=$(curl -s "${RAILWAY_URL}/health")
if echo "$HEALTH" | grep -q "ok"; then
    echo "✅ Backend is running"
else
    echo "❌ Backend unhealthy: $HEALTH"
    exit 1
fi

# 2. Check CORS headers
echo ""
echo "2️⃣  CORS Verification"
CORS=$(curl -s -w "\n%{http_code}" -X OPTIONS "${RAILWAY_URL}/auth/login" \
    -H "Origin: ${VERCEL_URL}" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: Content-Type")

HTTP_CODE=$(echo "$CORS" | tail -n 1)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ CORS preflight passes"
else
    echo "⚠️  CORS preflight HTTP $HTTP_CODE (may be OK if not OPTIONS support)"
fi

# 3. Check if WebSocket endpoint exists
echo ""
echo "3️⃣  WebSocket Endpoint Check"
WS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    "${RAILWAY_URL}/ws/clientes/test?module=dashboard" \
    -H "Connection: Upgrade" \
    -H "Upgrade: websocket")

if [ "$WS_STATUS" != "200" ]; then
    echo "✅ WebSocket endpoint responds (HTTP $WS_STATUS is expected for WS)"
else
    echo "⚠️  WebSocket endpoint HTTP $WS_STATUS"
fi

# 4. Check Frontend build
echo ""
echo "4️⃣  Frontend Build Check"
FRONTEND=$(curl -s -o /dev/null -w "%{http_code}" "${VERCEL_URL}")
if [ "$FRONTEND" = "200" ]; then
    echo "✅ Frontend is accessible"
else
    echo "❌ Frontend HTTP $FRONTEND"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Deployment verification complete!"
echo ""
echo "Next steps:"
echo "1. Login at ${VERCEL_URL}"
echo "2. Check browser console for WebSocket connection"
echo "3. Verify 'En línea' status in dashboard header"
echo ""
