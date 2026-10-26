# API RP 520 sizing integration

The project now exposes the independently callable API RP 520 Seventh Edition
(January 2000) sizing primitives used at the API 581 pressure-relief-device
boundary:

- critical pressure ratio and gas/vapor coefficient `C`;
- relieving pressure;
- critical and subcritical gas/vapor effective area;
- certified/non-certified liquid effective area with supplied correction factors;
- liquid viscosity correction `K_v`.

The source document is `api-rp-520-1.pdf` in the project root.  Calculations
use SI inputs where stated, preserve the supplied correction factors, and return
typed results through the normal `api581.evaluate()` envelope. API 526 orifice
selection, manufacturer capacity certification, two-phase DIERS sizing, and
installation pressure-drop qualification remain separate engineering activities.
