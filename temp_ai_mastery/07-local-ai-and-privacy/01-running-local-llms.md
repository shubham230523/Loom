# Local AI & Privacy: Running Offline LLMs

For enterprise developers or those working on sensitive projects, data privacy is paramount. Running Large Language Models (LLMs) locally ensures that your source code, configuration files, and proprietary logic never leave your machine.

## Why Go Local?
- **Zero Data Leakage:** Code and context remain entirely offline.
- **Cost Efficiency:** No per-token costs once the hardware is set up.
- **Independence:** Work without an internet connection or reliance on third-party API availability.
- **Low Latency:** Faster response times for simple tasks on powerful local hardware.

---

## 1. Setting Up Local Inference Engines

### Ollama (Easiest for Most)
Ollama is a lightweight, easy-to-use tool for running LLMs on macOS, Linux, and Windows.
- **Installation:** Download from [ollama.com](https://ollama.com).
- **Run a Model:**
  ```bash
  ollama run deepseek-coder:6.7b
  ```

### vLLM (High Throughput for Servers)
If you are running models on a dedicated local server with high-end GPUs, vLLM is optimized for performance.
- **Setup:**
  ```bash
  pip install vllm
  python -m vllm.entrypoints.openai.api_server --model deepseek-ai/deepseek-coder-33b-instruct
  ```

---

## 2. Specialized Coding Models

For the best experience, use models specifically fine-tuned for software engineering:

- **DeepSeek-R1 / Coder:** Currently one of the top-performing open-source coding models, often rivaling GPT-4 in specific programming tasks.
- **Qwen 2.5 Coder:** Alibaba's latest coding model, excellent at a wide range of languages including Rust and Kotlin.
- **Codestral (Mistral AI):** A high-performance model optimized specifically for FIM (Fill-In-the-Middle) tasks.

---

## 3. Connecting Local Models to Your IDE

Most modern AI extensions support "Custom API Endpoints," allowing you to point them at your local Ollama or vLLM instance.

### VS Code (Continue / Roo Code)
1. Install the **Continue** extension.
2. In `config.json`, add your local provider:
   ```json
   {
     "models": [{
       "title": "Ollama DeepSeek",
       "provider": "ollama",
       "model": "deepseek-coder:6.7b"
     }]
   }
   ```

### Cursor
1. Go to **Settings > Models**.
2. Toggle "Override OpenAI Base URL".
3. Enter your local endpoint (e.g., `http://localhost:11434/v1` for Ollama).

### Android Studio (Gemini / Custom Plugins)
Use plugins like **Codeium** or **Continue** (via the JetBrains marketplace) to connect to your local server following similar configuration steps as VS Code.

---

## Hardware Recommendations
- **Minimum:** 16GB RAM (8GB models like Llama 3 or DeepSeek 7B).
- **Recommended:** 32GB+ RAM or Apple Silicon (M2/M3 Pro/Max) for 30B+ parameter models.
- **Pro:** Dedicated NVIDIA RTX 3090/4090 for fast, high-throughput inference.
