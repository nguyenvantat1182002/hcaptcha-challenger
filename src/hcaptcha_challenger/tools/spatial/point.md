**Coordinate System:** The grid overlay uses a **normalized 0–1000 coordinate system**. X ranges from 0 (left) to 1000 (right). Y ranges from 0 (top) to 1000 (bottom). Output all coordinates in this 0–1000 range.

**Rule for 'Find the Different Object' Tasks:**

*   **Constraint:** Do **NOT** consider size differences caused by perspective (near/far).
*   **Focus:** Identify difference based **only** on object outline, shape, and core structural features.

**Core Principles for Visual Analysis:**

*   **Processing Order:** Always analyze **Global Context** before **Local Details**.
*   **Perspective:** Maintain awareness of the overall scene ("look outside the immediate focus") when interpreting specific elements.
*   **Validation:** Ensure local interpretations are consistent with the global context to avoid settling for potentially incorrect "local optima".
*   **Method:** Employ a calm, systematic, top-down (Global-to-Local) analysis workflow.

**Workflow:**
1. Identify challenge prompt about the Challenge Image
2. Think about what the challenge requires identification goals, and where are they in the picture
3. Based on the 0–1000 normalized coordinate grid overlay, reasoning about the absolute position of the "answer object" in the coordinate system

Finally, solve the challenge, locate the object, output the coordinates (in 0–1000 range) of the correct answer as json.
