# G30 bounded CPU profile

This is a separate revision-2 metadata profile for the pinned Qwen3-0.6B candidate. It preserves the original G27 manifest, source commit, operator identities, tokenizer/config/template identities, and advertised weight identity. The new role component binds the candidate to the unchanged G27 parent manifest by its complete EYL SHA256.

The profile records four optional proposal interfaces: reasoning, planning, specialist, and critic. The critic accepts a bounded candidate/evidence pair and returns unverified text under `evaluation.proposal.v1`; it does not emit a numeric score, verdict, or action. Defaults remain unset. Role intent grants no execution permission or quality claim.

The initial owned CPU envelope is batch one, at most 64 context positions and eight generated tokens per accepted job, under the manifest's wider declared limits. Unsupported architecture, precision, tokenizer identity, role, or capacity must fail closed. The parent tokenizer and its bytes remain separately identified. This catalog entry alone does not enable local execution.

Weights are not part of this catalog repository. The pinned whole-file SHA256 and size remain publisher-advertised until a separate bounded local acceptance verifies actual bytes. Model execution, numerical equivalence to upstream, latency, fit, role quality, GPU, and training are `not_run` here. The serialized profile and EYL record are intent/provenance only.
