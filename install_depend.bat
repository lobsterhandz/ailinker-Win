@echo off
REM Install script for Windows - Sets up RabbitMQ and dependencies

echo Installing RabbitMQ...
winget install RabbitMQ

echo Configuring RabbitMQ service...
rabbitmqctl add_user user 123456  
rabbitmqctl set_permissions -p / user ".*" ".*" ".*"
rabbitmqctl set_user_tags user administrator

echo Installing libopus (Not required on Windows, alternative needed)
REM If needed, install libopus for Windows manually

echo Installation completed successfully!
pause
