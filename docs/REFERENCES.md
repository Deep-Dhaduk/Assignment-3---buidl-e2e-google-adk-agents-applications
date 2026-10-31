# References and adaptation notes

This implementation is written for the assignment using the public APIs of its dependencies. It follows architectural ideas from the supplied references; no reference repository was copied wholesale. Dependency packages retain their own licenses. If you later copy upstream source, preserve its applicable notices and license requirements.

| Part | Supplied references | This implementation and differences |
|---|---|---|
| a | [Google deep research article](https://cloud.google.com/blog/products/ai-machine-learning/build-a-deep-research-agent-with-google-adk), [leadGenerationAgentADK](https://github.com/MagnIeeT/leadGenerationAgentADK) | Interactive profile discovery, sequential research/verification and report export. Uses a smaller workflow to keep local demonstrations understandable and model usage bounded. |
| b | [gemini-cli-on-adk](https://github.com/derrickchwong/gemini-cli-on-adk) | Real non-interactive Gemini CLI as an ADK tool. Supplies registered source files through stdin and denies CLI tools; arbitrary shell execution and repository editing are intentionally outside its scope. Cloud Run configuration is provided as a container, not deployed. |
| c | [Google tools article](https://cloud.google.com/blog/topics/developers-practitioners/tools-make-an-agent-from-zero-to-assistant-with-adk), [software-bug-assistant](https://github.com/google/adk-samples/tree/main/python/agents/software-bug-assistant) | Real MCP server with seeded bug database and sample source. Does not connect to GitHub issues, StackOverflow or the reference's PostgreSQL MCP Toolbox service. |
| d | [Code review codelab](https://codelabs.developers.google.com/adk-code-reviewer-assistant/instructions?hl=en), [reference repository](https://github.com/ayoisio/adk-code-review-assistant) | AST analysis, Ruff, actual unittest execution, ADK synthesis, validation, traces, API and tests. Restricted sample registry; no arbitrary repository review or cloud execution platform. |
| e | [Sports-store codelab](https://codelabs.developers.google.com/codelabs/sports-agent-adk-mcp-alloydb?hl=en), [reference repository](https://github.com/mtoscano84/sports-agent-adk-mcp-alloydb/) | MCP catalog lookup and transactional orders. Local SQLite plus configurable PostgreSQL driver. No managed AlloyDB/Toolbox deployment, nearby-store search, embedding search or payment processing. |

Confirm with the instructor if exact reproduction of managed services is required. The assignment names the references as hints, but this repository does not claim that local substitutions are identical to the referenced cloud architecture.

API references consulted:

- [ADK Python quickstart](https://google.github.io/adk-docs/get-started/python/)
- [ADK MCP tools](https://google.github.io/adk-docs/tools-custom/mcp-tools/)
- [ADK function tools](https://google.github.io/adk-docs/tools-custom/function-tools/)
- [Gemini CLI headless mode](https://geminicli.com/docs/cli/headless/)
- [Gemini CLI policy engine](https://geminicli.com/docs/reference/policy-engine/)

The tested dependency versions are pinned in `requirements.lock` and `package-lock.json`. Current online documentation may describe a newer major ADK release; use the installed package and tests when maintaining this ADK 1.x implementation.
