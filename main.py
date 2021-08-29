from asyncio.unix_events import AbstractChildWatcher
from websockets import client
from bilibili_api.live import LiveDanmaku
import json
import asyncio
import sys

bot_data = {
    'session': ''
}


def gen_message(target: int, text: str):
    data_body = {
        'sessionKey': bot_data['session'],
        'target': target,
        'messageChain': [{'type': 'Plain', 'text': text}]
    }
    msg_body = {
        'syncId': 'sendGroupMessage',
        'command': 'sendGroupMessage',
        'subCommand': None,
        'content': data_body
    }
    return json.dumps(msg_body)


async def main():
    # 加载配置
    config_file = open('./config.json', encoding='utf8', mode='r')
    config = json.load(config_file)
    API_URL: str = config['api_url']
    AUTH = config['auth_key']
    QQ = config['qq']
    GROUPS = config['groups']
    TEXT = config['text']
    config_file.close()
    # 登陆 mriai 接口
    ws = await client.connect(API_URL+f'/message?verifyKey={AUTH}&qq={QQ}')
    session_info = json.loads(await ws.recv())['data']
    if session_info['code'] == 0:
        print('Auth succeed')
        bot_data['session'] = session_info['session']
        for v in GROUPS:
            pass
            # await ws.send(gen_message(v,'机器人上线'))
    else:
        print('Auth failed')
        sys.exit(0)
    live_danmaku = LiveDanmaku(config['room_id'], max_retry=5000)

    @live_danmaku.on('LIVE')
    async def live(arg):
        for v in GROUPS:
            await ws.send(gen_message(v, TEXT))

    danmaku = asyncio.create_task(live_danmaku.connect())
    # 用来检查bot是否运行的命令

    async def group_message_handler():
        while True:
            messages = json.loads(await ws.recv())['data']
            if messages['type'] == 'GroupMessage' and messages['sender']['group']['id'] in GROUPS and messages['messageChain'][1]['type'] == 'Plain' and messages['messageChain'][1]['text'] == '/botStatus':
                await ws.send(gen_message(messages['sender']['group']['id'], '开播通知机器人运行中'))
            await asyncio.sleep(0.5)

    msg_task = asyncio.create_task(group_message_handler())

    # 心跳
    async def heartbeat():
        msg = {
            "syncId": 123,
            "command": "about",
            "subCommand": None,
            "content": {
                "sessionKey":bot_data['session']
            }
        }
        while True:
            await ws.send(json.dumps(msg))
            await asyncio.sleep(60)
            print('心跳')

    heartbeat_task = asyncio.create_task(heartbeat())

    await danmaku
    await msg_task
    await heartbeat_task

if __name__ == '__main__':
    asyncio.run(main())
