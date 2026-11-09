# Source mapping and provenance

## Current source state

The repository currently has a user-provided summary naming Kim et al., *Nanoscale Torsional Optomechanics*, arXiv:1210.1852v2, and reporting several experimental values. The actual PDF is not stored here and page-level passages are not available in a directly readable source form. Therefore:

- source identity and all numeric reference values are marked `USER_SUPPLIED_NOT_VERIFIED_NOT_RUNTIME_PARAMETERS`;
- no value is represented as a measurement by this software or by HARDAM;
- add the actual source PDF and record page/figure/table locations before changing provenance to independently verified;
- technical analogies in the architecture are explicitly design choices, not claims attributed to the paper.

## Mapping table

| Reported physical concept | Proposed software analogy | Evidence class | Prohibited inference |
| --- | --- | --- | --- |
| Optical resonator and evanescent coupling | Sensor input interface | Analogy | The paper defines an AI sensor layer. |
| Photodiode AC/DC signals | Distinct normalized observation channels | Analogy | Software channels are photodiode measurements. |
| Resonance slope and signal quality | Explainable evidence ranking | Analogy | Optical slope performs cognitive attention. |
| Mechanical resonance modes | State representation / mode classification | Analogy | Mechanical modes are internal AI states. |
| FEM analysis | Model-based reasoning component | Analogy | FEM is equivalent to an AI brain. |
| Thermomechanical calibration | Uncertainty discipline | Analogy | Physical calibration directly calibrates LLM confidence. |
| Experimental record | Provenance-bearing memory | Analogy | Reference values were measured by HARDAM. |

## User-supplied experimental values

The fallback YAML stores these as reference metadata only: disk diameter 10 μm; gap 100 nm; displacement noise 7 fm/√Hz; angular displacement noise 4 nrad/√Hz; torque sensitivity 4×10⁻²⁰ N·m/√Hz; Q approximately 4000 in vacuum and 150 in air; optical power up to 20 μW; pressure approximately 10⁻⁶ torr. These are not runtime parameters and require source-page verification.
