# SiluetBot

This is the bot to control the smart home. The main function is to receive the humidity temperature and other parameters from the sensor, the transfer of photos from cameras and users warning about negative situations.

## Installation

Pip:
	`sudo apt-get install python3-pip`

Install driver [mysqlclient](https://github.com/PyMySQL/mysqlclient-python):
	`sudo apt-get install python-dev libmysqlclient-dev`
	`sudo pip3 install mysqlclient`

Via pip:
- [python-telegram-bot](https://pypi.python.org/pypi/python-telegram-bot/#installing)
	`sudo pip3 install python-telegram-bot`

- [requests](http://docs.python-requests.org/en/master/user/quickstart/)
	`sudo pip3 install requests --upgrade`

- PyYAML
	`sudo pip3 install PyYAML`


From githab.com:
- [emoji](https://github.com/carpedm20/emoji)
	`sudo git clone https://github.com/carpedm20/emoji.git`
	`cd emoji`
	`sudo python3 setup.py install`
Add autostart:
	`sudo nano /etc/rc.local`
	add:
	"cd ~/SiluetBot/"
	"/usr/bin/python3.5 ~/SiluetBot/SiluetBot.py 1 > /dev/null 2 > /dev/null &"

## Requirements
- Python 3

## Autostart
`sudo nano /etc/rc.local`

And added:

`cd /home/pi/SiluetBot/`

`/usr/bin/python3.4 /home/pi/SiluetBot/SiluetBot.py 1 > /dev/null 2 > /dev/null &`

