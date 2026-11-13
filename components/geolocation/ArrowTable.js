// Minimal stand-in for the ArrowTable export of streamlit-component-lib
// (Apache-2.0, streamlit-component-lib 2.0.0, vendored in streamlit.js).
//
// EarthWise's geolocation component never passes dataframes — its args are
// plain JSON (request/request_id) and its value is plain JSON (status /
// latitude / longitude) — so the real ArrowTable implementation is never
// used. This stub exists only so streamlit.js's static
// `import { ArrowTable } from "./ArrowTable"` resolves without pulling in
// the large `apache-arrow` package. It must not be used for real tables:
// constructing one throws loudly instead of silently misbehaving.
export class ArrowTable {
  constructor() {
    throw new Error(
      "ArrowTable stub: this component does not support dataframes"
    );
  }
  serialize() {
    throw new Error(
      "ArrowTable stub: this component does not support dataframes"
    );
  }
}
