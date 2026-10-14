# eylema-models

Model metadata and accepted model-set manifests. [Türkçe](README.tr.md).

**Status: pinned G27 candidate catalog and nine optional role-interface records, with an offline development audit.** Actual production Rust manifest checks live in core; no weights, tokenizer/model execution, benchmark or trained model is delivered.

[Catalog/contract notes](docs/en/model-catalog.md) · [Qwen candidate](catalog/qwen3-0.6b.v1.json) · [Role interfaces](contracts/role-interfaces.v1.json). `python tools/model_catalog.py --check` checks declared JSON/EYL/source/role/operator consistency; it is development tooling, not inference.

## Scope

Catalog source revisions, hashes, licenses, operator requirements and evaluation references. Keep the canonical model-set schema in eylema until a separately versioned contract is justified. Metadata registration is not execution or acceptance.

Production Rust code, shared types, runtime/model execution and the CLI stay in [eylema](https://github.com/eylema-dev/eylema); product contracts live in [English docs](https://github.com/eylema-dev/eylema-docs-en) and [Turkish docs](https://github.com/eylema-dev/eylema-docs-tr). [The repository map](https://github.com/eylema-dev/devguide/blob/main/docs/en/repository-map.md) defines the boundaries.

## First acceptance gate

Before implementation, open a scoped task with input/output contracts, an exact core revision, meaningful failure cases, dependency inventory and named execution targets. Replace the documentation-only source guard with suitable tests in the same PR that introduces implementation. Documentation CI is not runtime or hardware evidence.

Use [CONTRIBUTING](CONTRIBUTING.md) and [AGENTS](AGENTS.md). Keep private data, credentials, operational records and model weights outside Git. Public artifacts need their own approved storage, provenance and license decision; no store or service is provisioned here. First-party source and documentation are licensed under [Apache-2.0](LICENSE). Separately identified third-party material, model weights and datasets retain their own terms.

G56 adds the [declared decision-score candidate and synthetic reference](docs/en/decision-score-profile.md); owned Rust decodes its metadata, native scoring/model quality remains unsupported/not_run.

G67 adds a [declared embedding profile](docs/en/embedding-profile.md), independent synthetic pooling/L2/retrieval references and real core EYL fixture tests. Native model/Turkish-quality execution remains not_run under G68.
