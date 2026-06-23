import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { compile } from "json-schema-to-typescript";

const here = dirname(fileURLToPath(import.meta.url));
const backend = resolve(here, "../../backend");
const outFile = resolve(here, "../src/types/ws.ts");

const schemaJson = execFileSync(
  "uv",
  ["run", "--project", backend, "python", "scripts/export_ws_schema.py"],
  { cwd: backend, encoding: "utf8" },
);

const schema = JSON.parse(schemaJson);
for (const def of Object.values(schema.$defs)) {
  for (const property of Object.values(def.properties ?? {})) delete property.title;
}

const banner = [
  "/**",
  " * AUTO-GENERATED from the backend pydantic wire models (morse_decoder.api.wire).",
  " * Do not edit by hand — run `npm run gen:ws-types`.",
  " */",
].join("\n");

const ts = await compile(schema, "ServerMessage", {
  bannerComment: banner,
  additionalProperties: false,
  declareExternallyReferenced: true,
});

writeFileSync(outFile, ts);
