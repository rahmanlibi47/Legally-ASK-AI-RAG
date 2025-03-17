# LLaMA Model Setup Instructions

## Prerequisites
1. You need to request access to LLaMA 2 from Meta AI by visiting: https://ai.meta.com/llama/
2. Once approved, you'll receive an email with download instructions.

## Download Instructions
1. Create a directory named `llama-2` inside this `models` folder
2. Download the following files from Meta's provided link and place them in the `llama-2` directory:
   - `config.json`
   - `pytorch_model.bin`
   - `tokenizer.json`
   - `tokenizer_config.json`

## Model Variants
You can choose from different sizes of LLaMA 2 models:
- 7B parameters (recommended for local usage)
- 13B parameters
- 70B parameters

Choose based on your hardware capabilities. The 7B model requires at least 16GB of RAM.

## Directory Structure
After downloading, your directory structure should look like this:
```
models/
└── llama-2/
    ├── config.json
    ├── pytorch_model.bin
    ├── tokenizer.json
    └── tokenizer_config.json
```

## Additional Notes
- Make sure you have enough disk space (approximately 15GB for the 7B model)
- The model files will be loaded automatically by the LLMService class
- Keep the model files in this directory for offline usage