import re
import subprocess
import time
import requests
from requests.exceptions import ConnectionError

from adslproxy.db import RedisClient
from adslproxy.config import *


class Sender():
    def __init__(self):
        self.redis = RedisClient()

    def get_ip(self, ifname=ADSL_IFNAME):
        (status, output) = subprocess.getstatusoutput('ifconfig')
        if status == 0:
            pattern = re.compile(ifname + '.*?inet.*?(\d+\.\d+\.\d+\.\d+).*?netmask', re.S)
            result = re.search(pattern, output)
            if result:
                ip = result.group(1)
                return ip

    def adsl(self):
        while True:
            print('ADSL Start, Remove Proxy, Please wait')
            self.redis.remove(CLIENT_NAME)
            (status, output) = subprocess.getstatusoutput(ADSL_BASH)
            if status == 0:
                print('ADSL Successfully')
                ip = self.get_ip()
                if ip:
                    print('Now IP', ip)
                    try:
                        print('Testing Proxy, Please Wait')
                        proxy = '{ip}:{port}'.format(ip=ip, port=PROXY_PORT)
                        print('Proxy', proxy)
                        response = requests.get(TEST_URL, proxies={
                            'http': 'http://' + proxy,
                            'https': 'https://' + proxy
                        })
                        if response.status_code == 200:
                            self.redis.set(CLIENT_NAME, proxy)
                            time.sleep(ADSL_CYCLE)
                    except ConnectionError:
                        print('Invalid Proxy, Re Dialing')
                else:
                    print('Get IP Failed, Re Dialing')
                    time.sleep(ADSL_ERROR_CYCLE)
            else:
                print('ADSL Failed, Please Check')
                time.sleep(ADSL_ERROR_CYCLE)


def run():
    sender = Sender()
    sender.adsl()


if __name__ == '__main__':
    run()