# Workflow de la Operación — Resolución de Cuentas Morosas
## Flujo de trabajo por roles · Law Offices Santiago

Este documento describe **cómo se mueve cada cuenta** por el equipo, de principio a fin, con el rol dueño de cada paso y los puntos de decisión. Acompaña al Plan Maestro (`plan-maestro-junta.md`) y al Plan de Ejecución (`plan-resolucion-cuentas-morosas.md`).

---

## 1. Roles en el flujo

| Símbolo | Rol | Función en el flujo |
|---------|-----|---------------------|
| **CONT** | Jefe(a) de Contabilidad (líder) | Dirige, integra números, reporta a la Junta |
| **CxC** | Coordinadores de Cuentas por Cobrar (2) | Arman expedientes, priorizan, gestionan planes de pago, mantienen el tablero |
| **LEGAL** | Abogado(a) revisor(a) | Decide cobrar vs. retirar; prepara y firma mociones |
| **COBRO** | Encargado(a) de cobranza (+ apoyo temporal) | Contacta clientes, negocia y cobra |

---

## 2. Diagrama del flujo (de la cuenta a la resolución)

```
      ┌──────────────────────────────────────────────────────────────┐
      │                    CUENTA VENCIDA (1 de ~800)                 │
      └───────────────────────────────┬──────────────────────────────┘
                                       │
   ETAPA 1 · IDENTIFICACIÓN            ▼
   [CONT + CxC]           ┌────────────────────────────┐
                          │ Cargar cuenta al tablero:  │
                          │ saldo, contrato, cliente   │
                          └──────────────┬─────────────┘
                                         │
   ETAPA 2 · EXPEDIENTE Y PRIORIZACIÓN   ▼
   [CxC]                  ┌────────────────────────────────────────┐
                          │ Armar expediente:                      │
                          │ • Devengado vs. no devengado           │
                          │ • PRÓXIMA AUDIENCIA (campo crítico)    │
                          │ • ¿Cliente localizable?                │
                          │ Prioridad: P1 (≤30d) / P2 / P3         │
                          └──────────────┬─────────────────────────┘
                                         │
   ETAPA 3 · REVISIÓN LEGAL              ▼
   [LEGAL]                    ◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇
                          ◇  ¿CONVIENE RETIRARSE?  ◇
                             ◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇◇
                          │                        │
              NO (cobrar) │                        │ SÍ (retirar)
                          ▼                        ▼
   ETAPA 4A · COBRAR                 ETAPA 4B · RETIRARSE
   [COBRO + CxC]                     [LEGAL + CxC]
   ┌────────────────────────┐        ┌────────────────────────────┐
   │ • Contacto multicanal  │        │ • Aviso al cliente         │
   │ • Estado de cuenta     │        │ • Reembolsar no devengado  │
   │ • Plan de pago/acuerdo │        │ • Moción de retiro + serv. │
   │ • Reenganchar el caso  │        │ • Permiso del Juez         │
   └───────────┬────────────┘        └─────────────┬──────────────┘
               │                                    │
               │  ¿Paga / acuerda?                  │  ¿Juez concede?
               │  Sí → resuelto                     │  Sí → resuelto
               │  No → escalar a LEGAL ─────────────┤  No → comparecer y reintentar
               ▼                                    ▼
   ETAPA 5 · CIERRE Y REPORTE
   [CONT]                 ┌────────────────────────────────────────┐
                          │ • Verificar expediente completo        │
                          │ • Marcar RESUELTO en el tablero        │
                          │ • Incluir en reporte mensual a Junta   │
                          └────────────────────────────────────────┘
```

---

## 3. Carriles (swimlanes) — quién hace qué en cada etapa

| Etapa | CONT (líder) | CxC (coordinadores) | LEGAL (abogado) | COBRO (cobranza) |
|-------|--------------|---------------------|-----------------|------------------|
| **1. Identificación** | Extrae y asigna la cartera | Cargan al tablero | — | — |
| **2. Expediente/prioridad** | Supervisa avance | **Arman expediente y priorizan por audiencia** | — | — |
| **3. Revisión legal** | — | Entregan expediente a Legal | **Deciden A o B** | — |
| **4A. Cobrar** | Monitorea metas | Dan seguimiento y registran | Aprueba descuentos/acuerdos | **Contacta y cobra** |
| **4B. Retirarse** | — | Preparan documentación de soporte | **Notifica, reembolsa, presenta y firma la moción** | — |
| **5. Cierre/reporte** | **Cierra y reporta a la Junta** | Verifican expediente completo | Confirma retiro concedido | — |

---

## 4. Puntos de decisión (dónde se define el rumbo)

1. **Prioridad (Etapa 2 · CxC):** ¿la próxima audiencia es en ≤30 días? → **P1, se atiende primero.**
2. **Cobrar o retirar (Etapa 3 · LEGAL):** el abogado decide según:
   - ¿Cuánto está devengado y es cobrable?
   - ¿El cliente responde y puede pagar?
   - ¿El retiro protege más a la firma que continuar?
   - ¿Hay tiempo para retirarse sin perjudicar al cliente antes de la audiencia?
3. **Resultado del cobro (Etapa 4A · COBRO):** si no paga ni acuerda → **escalar a Legal** para evaluar retiro.
4. **Resultado de la moción (Etapa 4B · LEGAL):** si el juez **niega** el retiro (audiencia muy próxima) → **comparecer** y reintentar después.

---

## 5. Reglas del flujo (no negociables)

- **Nada avanza a cobro o retiro sin pasar por la revisión legal** (Etapa 3). El abogado decide, no la cobranza.
- **Los P1 (audiencia ≤30 días) tienen prioridad absoluta** sobre cualquier otra cuenta.
- **En Vía B siempre se reembolsa lo no devengado** antes de cerrar.
- **Ninguna cuenta se cierra** (Etapa 5) sin expediente completo y verificado.
- **El tablero es la única fuente de verdad**: cada cuenta tiene dueño, etapa y próxima acción con fecha.

---

## 6. Cadencia de coordinación

| Reunión | Quién | Enfoque |
|---------|-------|---------|
| **Diaria (15 min)** | CONT + CxC + COBRO | Cuentas P1 con audiencia esta semana; bloqueos |
| **Revisión legal (según cola)** | LEGAL + CxC | Lote de expedientes listos para decisión A/B |
| **Semanal (60 min)** | Todo el equipo | Resueltos vs. meta; mociones pendientes; reembolsos; señales de riesgo |
| **Mensual** | CONT → Junta | Avance contra hitos y KPIs |

---

## 7. Handoffs (entregas entre roles) — para que nada se caiga

1. **CxC → LEGAL:** expediente completo con devengado/no devengado y fecha de audiencia. *Legal no recibe expedientes incompletos.*
2. **LEGAL → COBRO:** decisión "Vía A" con el monto cobrable y el margen de negociación aprobado.
3. **COBRO → CxC:** resultado del contacto (pagó / plan / no responde) para actualizar el tablero.
4. **LEGAL → CONT:** confirmación de retiro concedido para cerrar el caso.
5. **CxC → CONT:** expediente verificado para el reporte mensual.

---

*Anexo del Plan Maestro. Todos los pasos de retiro y cobranza se ejecutan bajo la aprobación del abogado revisor y conforme a las reglas de conducta profesional y del Immigration Court Practice Manual (EOIR).*
