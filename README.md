# AiLinker

[English](README.md) | [中文](README_CN.md)

## Introduction
### 1.1 System Features

* The system is developed based on Python 3.8, with decoupled design for large language models and backend voice services.
* Inter-node communication is based on the RabbitMQ framework.
* The system interfaces with hardware through WebSockets to implement AI chatbots, AI hardware control terminals, and other applications.
* The system aims to help beginners learn about online large model services, various voice service API calling processes, and hardware integration procedures.

### 1.2 Directory Structure
* common     # Common package directory
* configs    # Node configuration files directory
* scripts    # Related test scripts directory
* deploy     # Application deployment and background operation files directory
* docs       # Related documentation
* README.md  

### 1.3 Supported Hardware
* [AI-VOICE-Z01(Z02)](https://gitee.com/yumoutech/ai-devices/tree/master/ai-voice-z01)

## 2. Software Installation
### 2.1 System Software Installation
&nbsp;&nbsp;The software runs on Linux systems. Our test environment is Ubuntu 22.04, and we recommend beginners use the same version. <br>
Other Linux distributions can also follow this documentation to install related dependencies.

#### 1. Install RabbitMQ Server

```
$ sudo apt install rabbitmq-server
```

#### 2. Configure RabbitMQ Service:
```
$ sudo rabbitmqctl add_user user 123456
$ sudo rabbitmqctl set_permissions -p / user ".*" ".*" ".*"
$ sudo rabbitmqctl set_user_tags user administrator
```

#### 3. Install Other Dependencies
```
$ sudo apt install libopus-dev
```

### 2.2 Installing AILINKER

#### 1. Install Python Virtual Environment Management Tool (Miniconda or Conda Recommended)
* [Miniconda Installation Reference 1](https://www.cnblogs.com/jijunhao/p/17235904.html)
* [Conda Installation Reference 2](https://conda.io/projects/conda/en/latest/user-guide/install/index.html)

#### 2. Install Ailinker Backend Service

First ensure that the Conda virtual environment management tool is correctly installed

```
$ git clone https://gitee.com/yumoutech/ailinker.git
$ cd ailinker
$ ./install.sh
```

## 3. Running the Service

### 3.1 Preparation Before Running

&nbsp;&nbsp;Since the large model interface, speech recognition interface, and speech synthesis interface all use online service APIs, you need to apply for API keys from their respective official websites (see documentation in the docs directory for specific application methods), <br>
and enter the obtained information into the env_setup.bash file for normal operation. If this file doesn't exist, you can copy one from the docs directory using the following command.

```
# Make sure you're in the ailinker directory
$ cp docs/example_env_setup.bash env_setup.bash
```

The system defaults to using the openai-hk large model interface and Volcano Engine voice services. It's recommended to apply for these two first for testing. For specific application methods, check the introduction documents in the docs directory or click the links below:

1. [Apply for openai-hk large model API key](https://gitee.com/yumoutech/ailinker/blob/master/docs/%E5%A4%A7%E6%A8%A1%E5%9E%8Bapikey%E7%94%B3%E8%AF%B7%E8%AF%B4%E6%98%8E(openai-hk)%E4%B8%AD%E8%BD%AC%E5%B9%B3%E5%8F%B0.md)
2. [Apply for Volcano Engine voice service API key](https://gitee.com/yumoutech/ailinker/blob/master/docs/%E7%81%AB%E5%B1%B1%E5%BC%95%E6%93%8E%E8%AF%AD%E9%9F%B3%E6%9C%8D%E5%8A%A1apikey%E7%94%B3%E8%AF%B7%E8%AF%B4%E6%98%8E.md)

### 3.2 Running RabbitMQ Service

Theoretically, RabbitMQ service starts automatically after installation. Let's check its status to ensure it's running:

```
$ sudo service rabbitmq-server status
```

The output should show (running):

```
[sudo] password for deakin:
● rabbitmq-server.service - RabbitMQ Messaging Server
     Loaded: loaded (/lib/systemd/system/rabbitmq-server.service; enabled; vendor preset: enabled)
     Active: active (running) since Thu 2024-08-29 13:34:59 CST; 7h ago
   Main PID: 835 (beam.smp)
      Tasks: 27 (limit: 7084)
     Memory: 142.1M
        CPU: 35min 44.735s
     CGroup: /system.slice/rabbitmq-server.service
             ├─ 835 /usr/lib/erlang/erts-12.2.1/bin/beam.smp -W w -MBas ageffcbf -MHas ageffcbf -MBlmbcs 512 -MHlmbcs 512 -MMmcs 30 -P 1048576 -t 5000000 -stbt db -zdbbl 12800>
             ├─ 943 erl_child_setup 65536
             ├─1706 inet_gethost 4
             └─1707 inet_gethost 4

Aug 29 13:34:56 ubuntu22-VirtualBox systemd[1]: Starting RabbitMQ Messaging Server...
Aug 29 13:34:59 ubuntu22-VirtualBox systemd[1]: Started RabbitMQ Messaging Server.
```

If the service isn't running, start it with:

```
$ sudo service rabbitmq-server start
```

### 3.3 Running Ailinker Service in Foreground

```
$ conda activate ailinker
$ source env_setup.bash
$ python app.py
```

1. After the backend service starts, you can first access it using a computer browser. You will enter the backend management page (note that the page is still being updated, but this doesn't affect device usage).

2. If you have configured the board's IP and port information, restart the board and it will automatically connect to the service. Upon successful connection, the board's LED will flash purple. You can then try to wake up the device to start chatting.

### 3.4 Running Ailinker Service in Background (Don't start in background before device can chat)
During initial testing, it's better to start the service in the foreground to see debug information output. After testing is successful, you can enter the deploy directory and run the startup script to start the service in the background:

```
$ cd deploy
$ ./run_app.sh  # Press Enter after running
```

Check if the backend is running normally by viewing the log file in this directory:

```
$ cat app.log
```

The output should look like this:
```
2024-08-29 20:43:20,095-app-INFO: main app start...
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8090
 * Running on http://192.168.3.105:8090
Press CTRL+C to quit
```

## 4. Currently Supported Services

### Large Language Models

Currently only supports OpenAI SDK-compatible services, but some vendors' compatibility may be limited, potentially causing instability.

| LLM Service              | Supported | Compatibility | Performance                                                  | Model Effect            | Cost     |
| ----------------------- | --------- | ------------- | ------------------------------------------------------------ | ---------------------- | -------- |
| **OpenAI Proxy**        |           |               |                                                              |                        |          |
| gpt-4o                  | Yes       | Good          | Relatively stable, response speed depends on network and proxy service quality | Good, recommended      | High     |
| gpt-3.5-turbo          | Yes       | Good          | Relatively stable, response speed depends on network and proxy service quality | Average                | Low      |
| Other GPT models       | Yes       | Good          | /                                                            | /                      | /        |
|                        |           |               |                                                              |                        |          |
| **Alibaba Lingji Models** |           |               |                                                              |                        |          |
| Tongyi Qianwen         | Yes       | Average       | Average stability, faster response                           | Average understanding and logic | Low      |
| Other OpenAI SDK compatible models | Yes | Average    | /                                                            | /                      | /        |
|                        |           |               |                                                              |                        |          |
| **Zhipu AI**           | Coming    |               |                                                              |                        |          |
|                        |           |               |                                                              |                        |          |
| **Doubao LLM**         | Coming    |               |                                                              |                        |          |
|                        |           |               |                                                              |                        |          |

### Voice Services

| Voice Service                  | Supported | Performance                                                  | Effect                                           | Cost                           |
| ----------------------------- | --------- | ------------------------------------------------------------ | ------------------------------------------------ | ------------------------------ |
| **Volcano Engine**            |           |                                                              |                                                  |                                |
| Volcano Engine Speech Recognition | Yes     | Relatively stable, occasional slow response, rare disconnections | Average recognition, poor homophone handling      | Low, 20,000 free quota         |
| Volcano Engine Speech Synthesis | Yes      | Relatively stable, occasional slow response, rare disconnections | Good synthesis effect                            | Low, 20,000 free quota         |
| **iFlytek AI**                |           |                                                              |                                                  |                                |
| iFlytek Speech Recognition    | Testing   |                                                              |                                                  |                                |
| iFlytek Speech Synthesis      | Testing   |                                                              |                                                  |                                |

## More Information
* [Frequently Asked Questions (FAQ)](./docs/FAQ.en.md)

## Version History
* v0.3.12 - Latest version
* v0.3.11 - Updated queue buffer size and control data sending frequency
* v0.3.02 - Modified ASR node configuration, audio not saved by default
* v0.3.01 - Updated ASR single request data size 