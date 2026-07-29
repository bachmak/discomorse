import {execFileSync} from "node:child_process";
import {dirname, resolve} from "node:path";
import {fileURLToPath} from "node:url";
import {writeFileSync} from "node:fs";
import {compile} from "json-schema-to-typescript";

const here = dirname(fileURLToPath(import.meta.url));
const backend = resolve(here, "../../backend");
const outFile = resolve(here, "../src/types/ws.ts");

const BANNER = [
    "/**",
    " * AUTO-GENERATED from the backend pydantic wire models (morse_decoder.api.wire).",
    " * Do not edit by hand — run `npm run gen:ws-types`.",
    " */",
].join("\n");

const COMPILE_OPTIONS = {
    bannerComment: "",
    additionalProperties: false,
    declareExternallyReferenced: true,
};

function exportedSchemas() {
    const json = execFileSync(
        "uv",
        ["run", "--project", backend, "python", "scripts/export_ws_schema.py"],
        {cwd: backend, encoding: "utf8"},
    );
    return JSON.parse(json);
}

function stripPropertyTitles(schema) {
    for (const object of [schema, ...Object.values(schema.$defs ?? {})]) {
        for (const property of Object.values(object.properties ?? {})) {
            delete property.title;
        }
    }
}

const {server, client} = exportedSchemas();

const declarations = [];
for (const [fallbackName, schema] of [
    ["ServerMessage", server],
    ["ClientMessage", client],
]) {
    stripPropertyTitles(schema);
    declarations.push(await compile(schema, fallbackName, COMPILE_OPTIONS));
}

writeFileSync(outFile, [BANNER, ...declarations].join("\n"));
