# Sheremetyevo International Airport (SVO) schedule Telegram bot (Unofficial)
## Features 
+ Access to ***current schedule*** data and ***flight info***
+ Access to ***historical data*** and ***flight changes***
+ Search either through direct messages or using the ***inline method*** by multiple parameters:
  + Flight number
  + Destination (including IATA code)
  + Company (including IATA code)
  + Direction
  + Date (text or picker)
+ Convinient ***flight sharing*** through deep linking 
+ ***Store favorite*** flights 
## Stack
- Python 3.11+
- Asynchronous framework aiogram 3.0+
- MongoDB 
- [SvologAPI](https://svolog.ru/api/v1/docs) as data source
## How to Install (`long polling` update method)
1. Clone repository `git clone git@github.com:jktujg/svo-sked-bot.git`
2. Create bot via [BotFather](https://telegram.me/BotFather)
3. Turn on inline mode in bot settings
4. Create `.env` file in root directory and configure as in [example](./.example.env)
6. Run `docker compose up -d`
### Using `webhook` update method
For using this method, you need a running web server to which you need to connect an endpoint for receiving updates\
Then set `UPDATE_METHOD=webhook` and specify this web server and endpoint in `.env` file as shown below:
```shell
WEBHOOK_BASE=https://yourwebserver.com
WEBHOOK_ENDPOINT=/bot/webhook
WEB_SERVER_HOST=0.0.0.0
WEB_SERVER_PORT=7892
```
Also in the `docker-compose.yml` file for the `tg_bot` service you have to add
```
ports:
  - 127.0.0.1:7892:7892
```
This is necessary to prevent external access to the container while allowing access from the web server
## How to run tests 
1. Create virtual environment and install requirements
```shell
python -m venv .venv &&
. ./.venv/bin/activate &&
python -m pip install -r requirements.txt
```
2. Run test script `./test.sh <venv_activation_script> [<unittest_params>]`, for example
```shell
./test.sh .venv/bin/activate -v
```
## Todo
+ Flight update subscription
+ Access to seasonal schedule data

