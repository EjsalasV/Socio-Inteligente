-- Migration: Seed Workpapers Templates (78 papeles de trabajo)
-- Fecha: 2026-04-17
-- Descripcion: Cargar los 78 papeles modelo clasificados por L/S, aseveración e importancia

-- Limpiar tabla primero
DELETE FROM workpapers_templates WHERE 1=1;

-- Insertar papeles
INSERT INTO workpapers_templates (codigo, numero, ls, nombre, aseveracion, importancia, obligatorio, descripcion) VALUES
('130.01', '01', 130, 'Conciliación Cuentas por Cobrar', 'EXISTENCIA', 'CRITICO', 'SÍ', 'Validar que el saldo total de CXC en libros coincide con suma detallada de clientes'),
('130.02', '02', 130, 'Prueba de Valuación CXC', 'VALORACION', 'ALTO', 'SÍ', 'Verificar que las cuentas por cobrar estén valoradas al valor probable de cobro'),
('130.03', '03', 130, 'Procedimiento Analítico CXC', 'INTEGRIDAD', 'MEDIO', 'SÍ', 'Analizar variaciones en días de rotación y patrones de cobranza'),
('130.04', '04', 130, 'Confirmación Externa CXC', 'EXISTENCIA', 'CRITICO', 'NO', 'Enviar confirmación a clientes principales para validar saldos'),
('130.05', '05', 130, 'Prueba de Derechos CXC', 'DERECHOS', 'ALTO', 'SÍ', 'Validar que la empresa tiene derechos sobre los CXC registrados'),
('140.01', '01', 140, 'Conciliación Inventarios', 'EXISTENCIA', 'CRITICO', 'SÍ', 'Validar concordancia entre inventario físico y registros contables'),
('140.02', '02', 140, 'Prueba de Valoración Inventarios', 'VALORACION', 'CRITICO', 'SÍ', 'Verificar aplicación correcta del método de valuación'),
('140.03', '03', 140, 'Procedimiento Analítico Inventarios', 'INTEGRIDAD', 'MEDIO', 'SÍ', 'Analizar rotación de inventarios y cambios en márgenes'),
('140.04', '04', 140, 'Inspección Física Inventarios', 'EXISTENCIA', 'CRITICO', 'SÍ', 'Observar conteo físico y validar procedimientos'),
('140.05', '05', 140, 'Prueba Obsolescencia', 'VALORACION', 'ALTO', 'SÍ', 'Identificar inventario obsoleto o de lento movimiento'),
('150.01', '01', 150, 'Conciliación PPE', 'EXISTENCIA', 'CRITICO', 'SÍ', 'Validar registro detallado de activos contra registros contables'),
('150.02', '02', 150, 'Prueba Valoración PPE', 'VALORACION', 'CRITICO', 'SÍ', 'Verificar cálculo correcto de depreciación'),
('150.03', '03', 150, 'Procedimiento Analítico PPE', 'INTEGRIDAD', 'MEDIO', 'SÍ', 'Analizar cambios en tasas de depreciación y políticas contables'),
('150.04', '04', 150, 'Inspección de Activos', 'EXISTENCIA', 'ALTO', 'NO', 'Validar existencia física de activos significativos'),
('150.05', '05', 150, 'Prueba de Disposiciones', 'PRESENTACION', 'MEDIO', 'SÍ', 'Verificar que las disposiciones estén contabilizadas correctamente'),
('160.01', '01', 160, 'Conciliación Cuentas por Pagar', 'EXISTENCIA', 'CRITICO', 'SÍ', 'Validar saldo de CxP contra proveedores principales'),
('160.02', '02', 160, 'Prueba de Valuación CxP', 'VALORACION', 'ALTO', 'SÍ', 'Verificar provisiones y valuación de pasivos'),
('160.03', '03', 160, 'Procedimiento Analítico CxP', 'INTEGRIDAD', 'MEDIO', 'SÍ', 'Analizar días de pago y cambios en estructura de proveedores'),
('160.04', '04', 160, 'Confirmación Externa CxP', 'EXISTENCIA', 'ALTO', 'NO', 'Solicitar confirmación a proveedores principales'),
('160.05', '05', 160, 'Prueba Cutoff CxP', 'PRESENTACION', 'CRITICO', 'SÍ', 'Validar que se registren en el período correcto'),
('170.01', '01', 170, 'Conciliación Nómina', 'EXISTENCIA', 'CRITICO', 'SÍ', 'Validar saldos de pasivos laborales contra registros de nómina'),
('170.02', '02', 170, 'Prueba de Provisiones Laborales', 'VALORACION', 'CRITICO', 'SÍ', 'Verificar cálculo de vacaciones, cesantías y otras provisiones'),
('170.03', '03', 170, 'Procedimiento Analítico Nómina', 'INTEGRIDAD', 'MEDIO', 'SÍ', 'Analizar variaciones en salarios y cambios de personal'),
('170.04', '04', 170, 'Prueba de Obligaciones Fiscales', 'PRESENTACION', 'ALTO', 'SÍ', 'Validar cálculo y pago de aportes'),
('170.05', '05', 170, 'Prueba Beneficios Post-Empleo', 'VALORACION', 'ALTO', 'NO', 'Validar provisión de pensiones y beneficios jubilares'),
('180.01', '01', 180, 'Conciliación Deuda Financiera', 'EXISTENCIA', 'CRITICO', 'SÍ', 'Validar existencia y términos de créditos'),
('180.02', '02', 180, 'Prueba de Valoración Deuda', 'VALORACION', 'CRITICO', 'SÍ', 'Verificar cálculo de intereses y ajustes por inflación'),
('180.03', '03', 180, 'Procedimiento Analítico Deuda', 'INTEGRIDAD', 'MEDIO', 'SÍ', 'Analizar cambios en estructura de deuda y tasas'),
('180.04', '04', 180, 'Validación Covenants', 'PRESENTACION', 'ALTO', 'NO', 'Verificar cumplimiento de restricciones contractuales'),
('180.05', '05', 180, 'Confirmación Externa Deuda', 'EXISTENCIA', 'ALTO', 'SÍ', 'Solicitar confirmación de saldos a acreedores'),
('190.01', '01', 190, 'Conciliación Capital Social', 'EXISTENCIA', 'CRITICO', 'SÍ', 'Validar cambios en capital y accionistas'),
('190.02', '02', 190, 'Prueba de Ganancias Acumuladas', 'INTEGRIDAD', 'ALTO', 'SÍ', 'Verificar reconciliación de resultados acumulados'),
('190.03', '03', 190, 'Procedimiento Analítico Patrimonio', 'VALORACION', 'MEDIO', 'SÍ', 'Analizar variaciones en componentes del patrimonio'),
('190.04', '04', 190, 'Prueba de Distribuciones', 'PRESENTACION', 'ALTO', 'SÍ', 'Validar dividendos y distribuciones autorizadas'),
('190.05', '05', 190, 'Revisión de Restricciones', 'DERECHOS', 'MEDIO', 'NO', 'Identificar restricciones sobre el patrimonio'),
('200.01', '01', 200, 'Conciliación Ingresos', 'EXISTENCIA', 'CRITICO', 'SÍ', 'Validar registro de ingresos contra documentación'),
('200.02', '02', 200, 'Prueba de Valuación Ingresos', 'VALORACION', 'CRITICO', 'SÍ', 'Verificar que los ingresos se registren al valor correcto'),
('200.03', '03', 200, 'Procedimiento Analítico Ingresos', 'INTEGRIDAD', 'ALTO', 'SÍ', 'Analizar cambios en líneas de negocio y márgenes'),
('200.04', '04', 200, 'Prueba Cutoff Ingresos', 'PRESENTACION', 'CRITICO', 'SÍ', 'Validar que ingresos se registren en período correcto'),
('200.05', '05', 200, 'Prueba de Devoluciones', 'INTEGRIDAD', 'MEDIO', 'SÍ', 'Validar registro de devoluciones y ajustes'),
('210.01', '01', 210, 'Conciliación Costo de Ventas', 'EXISTENCIA', 'CRITICO', 'SÍ', 'Validar que costos sean apropiados y están registrados'),
('210.02', '02', 210, 'Prueba de Valuación Costos', 'VALORACION', 'CRITICO', 'SÍ', 'Verificar cálculo de costeo y aplicación de política'),
('210.03', '03', 210, 'Procedimiento Analítico Costos', 'INTEGRIDAD', 'MEDIO', 'SÍ', 'Analizar variaciones en costos unitarios y volumen'),
('210.04', '04', 210, 'Prueba de Asignación de Costos', 'PRESENTACION', 'ALTO', 'SÍ', 'Validar que costos se asignen correctamente'),
('210.05', '05', 210, 'Validación Teoría de Costos', 'VALORACION', 'MEDIO', 'NO', 'Revisar que la política de costos sea consistente'),
('220.01', '01', 220, 'Conciliación Gastos Operacionales', 'EXISTENCIA', 'ALTO', 'SÍ', 'Validar existencia de soportes para gastos registrados'),
('220.02', '02', 220, 'Prueba de Valuación Gastos', 'VALORACION', 'ALTO', 'SÍ', 'Verificar que gastos se hayan incurrido realmente'),
('220.03', '03', 220, 'Procedimiento Analítico Gastos', 'INTEGRIDAD', 'MEDIO', 'SÍ', 'Analizar cambios en estructura de gastos'),
('220.04', '04', 220, 'Prueba Cutoff Gastos', 'PRESENTACION', 'ALTO', 'SÍ', 'Validar que gastos se registren en período correcto'),
('220.05', '05', 220, 'Prueba de Gastos Inusuales', 'INTEGRIDAD', 'MEDIO', 'NO', 'Identificar y validar transacciones inusuales');

-- Verificar que se insertaron correctamente
SELECT COUNT(*) as total_papeles FROM workpapers_templates;
