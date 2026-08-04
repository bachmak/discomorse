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
    " * AUTO-GENERATED from the backend pydantic wire models (morse_decoder.api.messages).",
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

// A declaration starts a line, optionally behind its own doc comment.
const DECLARATION_START = /^(?=\/\*\*$|export )/m;
const DECLARED_NAME = /export (?:type|interface) (\w+)/;

// The two schemas share definitions - a channel name is one - and each compile
// spells its own out, so the second copy of a name is dropped.
function withoutRedeclarations(sources) {
    const seen = new Set();
    const kept = [];
    for (const block of sources.flatMap((source) => source.split(DECLARATION_START))) {
        const name = block.match(DECLARED_NAME)?.[1];
        if (seen.has(name)) continue;
        if (name) seen.add(name);
        kept.push(block);
    }
    return kept;
}

const {server, client} = exportedSchemas();

const compiled = [];
for (const [fallbackName, schema] of [
    ["ServerMessage", server],
    ["ClientMessage", client],
]) {
    stripPropertyTitles(schema);
    compiled.push(await compile(schema, fallbackName, COMPILE_OPTIONS));
}

writeFileSync(outFile, [BANNER, withoutRedeclarations(compiled).join("")].join("\n"));
