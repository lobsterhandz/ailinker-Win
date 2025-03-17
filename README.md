# AiLinker

[English](README.md) | [中文](README_CN.md)
# AILinker Refactor - Changelog

## 🔄 Summary of Changes
- **Switched from Linux to Windows** for development.
- **Added sentiment analysis** using DistilBERT.
- **Integrated DeepSeek or other Hugging Face models** for AI flexibility.
- **Implemented ESP32 eye controller** linked to chatbot responses.
- **Updated API routes and WebSocket** for successful chatbot communication with dual LCD eyes.

 **Final Outcome:** Faster, more interactive AI assistant with seamless ESP32 integration.


## Introduction
### 1.1 System Features

* The system is developed based on Python 3.8, with a modular architecture supporting both Linux and Windows environments.
* Support for large language models via **Hugging Face**, allowing both **local** and **API-based** model execution.
* Inter-node communication is based on the RabbitMQ framework.
* The system interfaces with hardware through WebSockets to implement AI chatbots, AI hardware control terminals, LED-based emotional response systems, and other applications.
* Enhanced compatibility with **Windows environments**, enabling simplified deployment via Python virtual environments and Windows Subsystem for Linux (WSL).
* Future-proof design supporting modular extensions for additional AI models, **local model execution**, and **API-based model integration**.

### 1.2 Directory Structure
* `common/` - Common package directory
* `configs/` - Node configuration files directory
* `scripts/` - Related test scripts directory
* `deploy/` - Application deployment and background operation files directory
* `docs/` - Related documentation
* `models/` - Hugging Face model storage (local execution support added)
* `README.md`  - Project documentation

### 1.3 Supported Hardware
* [AI-VOICE-Z01(Z02)](https://gitee.com/yumoutech/ai-devices/tree/master/ai-voice-z01)
* **Windows-based AI servers** supporting GPU acceleration for local models.
* LED eye display modules for **emotion-based animations** integrated via WebSockets.

## 2. Software Installation
### 2.1 System Software Installation
The software runs on both **Linux and Windows environments**.

#### 1. Install RabbitMQ Server
On **Ubuntu**:
```
$ sudo apt install rabbitmq-server
```
On **Windows** (using Chocolatey):
```
> choco install rabbitmq
```

#### 2. Configure RabbitMQ Service:
```
$ sudo rabbitmqctl add_user user 123456
$ sudo rabbitmqctl set_permissions -p / user ".*" ".*" ".*"
$ sudo rabbitmqctl set_user_tags user administrator
```

#### 3. Install Other Dependencies
On **Ubuntu**:
```
$ sudo apt install libopus-dev
```
On **Windows**:
```
> pip install opuslib
```

### 2.2 Installing AiLinker
#### 1. Install Python Virtual Environment Management Tool (Miniconda or Conda Recommended)
* [Miniconda Installation](https://docs.conda.io/en/latest/miniconda.html)

#### 2. Install AiLinker Backend Service
Ensure that the Conda virtual environment management tool is correctly installed:
```
$ git clone https://github.com/yourfork/ailinker.git
$ cd ailinker
$ ./install.sh
```
On **Windows**:
```
> git clone https://github.com/yourfork/ailinker.git
> cd ailinker
> install.bat
```

## 3. Running the Service
### 3.1 Preparation Before Running
AiLinker now supports **local execution of Hugging Face models** (Phi-2, Mistral, DeepSeek) and **API-based integration**.

To configure Hugging Face models, create the following environment variables:
```
HUGGINGFACE_API_KEY=<your_hf_api_key>
HUGGINGFACE_MODEL=<your_preferred_model>
```

Or, download a local model:
```
$ huggingface-cli download microsoft/phi-2 --local-dir ./models/phi-2
```

### 3.2 Running RabbitMQ Service
Check if RabbitMQ is running:
```
$ sudo service rabbitmq-server status
```
If not running, start it with:
```
$ sudo service rabbitmq-server start
```

### 3.3 Running AiLinker Service in Foreground
```
$ conda activate ailinker
$ python app.py
```
Once started, access the backend from a browser or API request. If configured correctly, the board's LED should flash purple, indicating successful connection.

### 3.4 Running AiLinker Service in Background
```
$ cd deploy
$ ./run_app.sh
```
To check logs:
```
$ cat app.log
```

## 4. Supported Features
### Large Language Models
| LLM Service | Supported | Compatibility | Performance | Model Effect | Cost |
|------------|-----------|--------------|------------|-------------|------|
| OpenAI GPT-4o | Yes | Good | Fast | High | High |
| OpenAI GPT-3.5 | Yes | Good | Medium | Average | Low |
| Hugging Face Phi-2 | Yes (Local) | Fast | High | Lightweight | Free |
| Hugging Face Mistral | Yes (Local) | Medium | High | Optimized for chat | Free |
| Hugging Face DeepSeek | Yes (Local) | Medium | High | Creative responses | Free |

### Voice Services
| Voice Service | Supported | Performance | Effect | Cost |
|--------------|-----------|------------|-------|------|
| Volcano Engine ASR | Yes | Stable | Moderate Accuracy | 20,000 free quota |
| Volcano Engine TTS | Yes | Stable | High Quality | 20,000 free quota |
| iFlytek ASR | Testing | TBA | TBA | TBA |
| iFlytek TTS | Testing | TBA | TBA | TBA |

### LED-Based Emotional AI Module (NEW)
* **WebSocket-based eye animation support for emotion-driven responses**.
* **Future FreeRTOS hooks for LED display integration**.
* **Supports emotion mapping for AI-generated responses** (e.g., happy, sad, neutral).

## More Information
For further details, check the [FAQ](./docs/FAQ.en.md).

## Version History
* v0.4.0 - Added support for Hugging Face models, Windows compatibility, and LED emotion display.
* v0.3.12 - Latest version with queue optimizations.
* v0.3.11 - Updated queue buffer size and control data sending frequency.
* v0.3.02 - Modified ASR node configuration, audio not saved by default.
* v0.3.01 - Updated ASR single request data size.

  ## Whats Next?
  * add blueprints for routes

