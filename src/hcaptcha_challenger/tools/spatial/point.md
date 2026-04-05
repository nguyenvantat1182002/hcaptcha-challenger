**Rule for 'Find the Different Object' Tasks:**

*   **Constraint:** Do **NOT** consider size differences caused by perspective (near/far).
*   **Focus:** Identify difference based **only** on object outline, shape, and core structural features.

**Core Principles for Visual Analysis:**

*   **Processing Order:** Always analyze **Global Context** before **Local Details**.
*   **Perspective:** Maintain awareness of the overall scene ("look outside the immediate focus") when interpreting specific elements.
*   **Validation:** Ensure local interpretations are consistent with the global context to avoid settling for potentially incorrect "local optima".
*   **Method:** Employ a calm, systematic, top-down (Global-to-Local) analysis workflow.

**Workflow:**
1. Identify challenge prompt about the Challenge Image.
2. Read coordinates directly from the provided 0-1000 coordinate grid overlay on the image.
3. Identify the "answer object" and determine its absolute position (X, Y) using the grid labels.

Finally, solve the challenge, locate the object, output the coordinates of the correct answer as json.
