from flask import Flask, render_template, request, session, make_response, jsonify
import requests
from lxml import html
import aiohttp
import asyncio
import time
import re
import pandas as pd

app=Flask(__name__)
app.secret_key = 'ali'


@app.route('/proxies')
def home():
    resposne=requests.get('https://free-proxy-list.net/')
    data_html=html.fromstring(resposne.content)
    proxies=[]
    data_xpath=data_html.xpath('//tr')
    for i in data_xpath:
        try:
            country=i.xpath('./td[4]/text()')
            ip = i.xpath('./td[1]/text()')
            port = i.xpath('./td[2]/text()')
            proxies.append(
                {'country':country[0],
                 'ip':ip[0],
                 'port':port[0]}
            )
        except:
            pass
    checked=health_check(proxies)
    final_result=clean_format(checked,proxies)
    df = convert_to_dataframe(final_result)
    temp = df.to_dict('records')
    columnNames = df.columns.values
    return render_template(
        'proxies.html',
        records=temp,
        colname=columnNames,
        num_proxies=len(proxies)
    )


def health_check(proxies):
    tasks = []

    async def fetch_page(url, proxyy):
        async with aiohttp.ClientSession() as session:
            try:
                start = time.time()
                async with session.get(
                        url,
                        proxy=proxyy,
                        timeout=5
                ) as response:
                # print(response.status)
                    return (
                        proxyy,
                        response.status,
                        time.time()-start
                    )
            except:
                return None

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for proxy in proxies:
        if "." in proxy['ip']:
            proxy_format='http://{}:{}'.format(
                proxy['ip'],
                proxy['port']
            )

            tasks.append(
                fetch_page(
                    'http://www.google.com/',
                    proxy_format
                )
            )
        else:
            pass
    res = loop.run_until_complete(asyncio.gather(*tasks))
    return res


def clean_format(checked,proxies):
    checked_json = {}
    final=[]
    for i in checked:
        if (i is not None) and (i[1] == 200):
            proxy_name = i[0]
            ip = re.findall('\/\/(.*?)\:', proxy_name)
            checked_json.update({ip[0]: i[2]})

    for p in proxies:
        for k,v in p.items():
            if v in checked_json:
                speed=round(checked_json[v],2)
                if speed < 1:
                    speed_str = "Very Fast"
                elif speed >1 and speed <2:
                    speed_str = "Fast"
                else:
                    speed_str ="Normal"
                final.append(
                    {'ip':p['ip'],
                     'country':p['country'],
                     'port':p['port'],
                     'response_time':round(checked_json[v],2),
                     'speed':speed_str,
                     }
                )
    return final


def convert_to_dataframe(final_result):
    df = pd.DataFrame.from_dict(
        final_result,
        orient="columns"
    )
    return df


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run()