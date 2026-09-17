#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const Module = require("module");

function deterministicRandom(seedText) {
    let seed = 2166136261;
    for (const character of seedText) {
        seed ^= character.charCodeAt(0);
        seed = Math.imul(seed, 16777619);
    }
    return function random() {
        seed += 0x6d2b79f5;
        let value = seed;
        value = Math.imul(value ^ (value >>> 15), value | 1);
        value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
        return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
    };
}

function documenterConfiguration(config) {
    const documentation = config.documentation.general;
    return {
        generic_visibility: documentation.generics,
        port_visibility: documentation.ports,
        signal_visibility: documentation.signals,
        constant_visibility: documentation.constants,
        type_visibility: documentation.types,
        function_visibility: documentation.functions,
        task_visibility: documentation.tasks,
        instantiation_visibility: documentation.instantiations,
        process_visibility: documentation.process,
        language: documentation.language,
        vhdl_symbol: documentation.symbol_vhdl,
        verilog_symbol: documentation.symbol_verilog,
        enable_fsm: documentation.fsm,
    };
}

async function main() {
    if (process.argv.length !== 3) {
        throw new Error("usage: export_teroshdl_docs.js PAYLOAD.json");
    }
    const payload = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
    process.env.NODE_PATH = [
        path.join(payload.extension, "out"),
        path.join(payload.extension, "node_modules"),
        process.env.NODE_PATH || "",
    ].join(path.delimiter);
    Module.Module._initPaths();

    const { Documenter } = require(path.join(
        payload.extension,
        "out/colibri/documenter/documenter"
    ));
    const { doc_output_type: outputType } = require(path.join(
        payload.extension,
        "out/colibri/documenter/common"
    ));
    const config = documenterConfiguration(JSON.parse(fs.readFileSync(payload.config, "utf8")));
    const results = [];

    for (const source of payload.sources) {
        Math.random = deterministicRandom(source.relative_path);
        const code = fs.readFileSync(source.path, "utf8");
        const documenter = new Documenter();
        const codeTree = await documenter.get_code_tree(code, source.language, config);
        if (!codeTree || !codeTree.name) {
            throw new Error(`TerosHDL could not find a design unit in ${source.relative_path}`);
        }
        const designUnit = codeTree.name;
        if (!/^[A-Za-z_][A-Za-z0-9_$]*$/.test(designUnit)) {
            throw new Error(`unsafe design-unit name '${designUnit}' in ${source.relative_path}`);
        }
        fs.mkdirSync(source.output_dir, { recursive: true });

        const markdown = await documenter.get_document(
            code,
            source.language,
            config,
            true,
            source.path,
            source.output_dir,
            false,
            outputType.MARKDOWN
        );
        const html = await documenter.get_document(
            code,
            source.language,
            config,
            true,
            source.path,
            source.output_dir,
            false,
            outputType.HTML
        );
        if (markdown.error || html.error) {
            throw new Error(`TerosHDL failed to document ${source.relative_path}`);
        }
        fs.writeFileSync(path.join(source.output_dir, "README.md"), markdown.document);
        fs.writeFileSync(path.join(source.output_dir, "index.html"), html.document);

        const svg = documenter.get_diagram_svg_from_code_tree(codeTree);
        if (svg) {
            fs.writeFileSync(path.join(source.output_dir, `${designUnit}.svg`), svg);
        } else if (codeTree.hdl_type !== "package") {
            throw new Error(`TerosHDL produced no interface SVG for ${source.relative_path}`);
        }
        results.push({ source: source.relative_path, design_unit: designUnit });
    }
    fs.writeFileSync(payload.result, JSON.stringify(results, null, 2) + "\n");
}

main().catch((error) => {
    console.error(`error: ${error.message}`);
    process.exitCode = 1;
});
