# AiLinker FAQ

## 1. Continuous Yellow Light Flashing
    Check the backend server address configuration and port availability. Cloud servers must have both ports 8090 and 9090 open - enable these in your cloud server control panel.

## 2. Purple Light Flashing but No Response
    1. Check backend logs for any exceptions
    2. Verify backend address configuration - in the ADDR field, only enter the IP address or domain name without adding http
    3. Cloud servers must have both ports 8090 and 9090 open

## 3. Audio Drops and Stutters with Long Text
    1. Ensure stable network connection
    2. Pull the latest backend code (issues were caused by insufficient device audio buffer - audio data transmission frequency has been increased) 