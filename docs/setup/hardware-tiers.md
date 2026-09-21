# Hardware Tiers and Model Selection

## Overview

The system detects available memory at setup and automatically selects an LLM model appropriate for your machine. The four hardware tiers are assumed starter values; the S1 spike verifies the model revision and final quantisation against tooling capabilities, documented in `docs/adr/llm-model-selection.md`.

## Supported Tiers

| Tier | Minimum Memory | Model | Quantisation |
|------|---|---|---|
| 64GB+ | 64 GiB | unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF | Q4_K_M |
| 48GB | 48 GiB | unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF | Q4_K_M |
| 32GB | 32 GiB | Qwen/Qwen3-14B-GGUF | Q4_K_M |
| 16GB | 16 GiB | Qwen/Qwen3-8B-GGUF | Q4_K_M |

Each tier also specifies a fallback model in case the primary model is unavailable.

## External Binary Requirements

The system requires two external binaries that are not Python packages:

### ffmpeg

Used for audio processing and format conversion.

**Detection:** The setup process will check for `ffmpeg` in your system PATH.

**Installation:** If `ffmpeg` is not found, the setup script will invoke your system package manager to install it automatically.

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install ffmpeg
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install ffmpeg
```

### whisper.cpp

A high-performance C++ implementation of OpenAI's Whisper model for speech-to-text.

**Detection:** The setup process will check for the `whisper-cpp` binary.

**Building from source:**

If `whisper.cpp` is not detected, you will need to build it from source:

```bash
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp
make main
# The binary will be at ./main, add to your PATH or copy to /usr/local/bin
```

The setup process will print detailed build instructions if the binary is not found.

## Doctor and Setup Commands

### make doctor

Checks your system configuration and reports:
- Detected system memory and matching hardware tier
- Presence and version of `ffmpeg`
- Presence and version of `whisper.cpp`
- Selected LLM model and quantisation
- Configuration file location and contents (if already set up)

**Exit codes:**
- 0: All components detected and configured correctly
- 1: One or more components are missing

Example output:
```
System Memory: 48 GiB
Hardware Tier: 48GB
LLM Model: unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF
Quantisation: Q4_K_M
ffmpeg: /usr/local/bin/ffmpeg (6.0)
whisper.cpp: /usr/local/bin/whisper-cpp (1.0.0)
Config: ~/.config/clinicloop/models.toml
```

### make setup

Performs the following setup steps:

1. **Detects hardware tier** based on available system memory
2. **Checks for external binaries:**
   - If `ffmpeg` is missing, invokes the system package manager to install it
   - If `whisper.cpp` is missing, prints build instructions (does not build automatically)
3. **Writes model selection** to `~/.config/clinicloop/models.toml`
   - Stores: tier label, model repository ID, quantisation method

The configuration file is used by later components (LLM factory) to load the correct model.

## Tier Selection Algorithm

The setup process selects a tier using this algorithm:

1. Detect available system memory in GiB
2. Find the highest-numbered tier where `min_gib ≤ available_memory`
3. If no tier matches (memory < 16 GiB), raise `UnsupportedMemoryTier` with the detected amount

This ensures that machines with exactly 48 GiB select the explicit 48GB tier, not the 32GB tier.

## Configuration

Model selection configuration is stored in `~/.config/clinicloop/models.toml`:

```toml
[model]
tier = "48GB"
repo_id = "unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF"
quantisation = "Q4_K_M"
```

This file is read by the LLM factory when initialising models for agent inference.

## Next Steps

After running `make setup`:

1. Download model weights from Hugging Face (as directed by the model repository)
2. Place weights in LM Studio or your configured model cache
3. Start LM Studio or your local inference server
4. Run `make doctor` to verify all components are operational

## See Also

- `docs/adr/llm-model-selection.md` – Decision record for model selection and tool-calling verification (S1)
- `docs/setup/problem-inventory.md` – Context for why local models are required
