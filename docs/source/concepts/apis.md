## APIs

A Llama Stack API is described as a collection of REST endpoints. We currently support the following APIs:

- **Inference**: run inference with a LLM
- **Safety**: apply safety policies to the output at a Systems (not only model) level
- **Agents**: run multi-step agentic workflows with LLMs with tool usage, memory (RAG), etc.
- **DatasetIO**: interface with datasets and data loaders
- **Scoring**: evaluate outputs of the system
- **Eval**: generate outputs (via Inference or Agents) and perform scoring
- **VectorIO**: perform operations on vector stores, such as adding documents, searching, and deleting documents
- **Telemetry**: collect telemetry data from the system

We are working on adding a few more APIs to complete the application lifecycle. These will include:
- **Batch Inference**: run inference on a dataset of inputs
- **Batch Agents**: run agents on a dataset of inputs
- **Post Training**: fine-tune a model
- **Synthetic Data Generation**: generate synthetic data for model development
