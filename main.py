from websockets import client
from bilibili_api.live import LiveDanmaku
import json
import asyncio

bot_data = {
    'session': ''
}


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
    live_danmaku = LiveDanmaku(config['room_id'], max_retry=5000)

    @live_danmaku.on('LIVE')
    async def live(arg):
        for v in GROUPS:
            data_body = {
                'sessionKey': bot_data['session'],
                'target': v,
                'messageChain': [{'type': 'Plain', 'text': TEXT}]
            }
            msg_body = {
                'syncId': 'sendGroupMessage',
                'command': 'sendGroupMessage',
                'subCommand': None,
                'content': data_body
            }
        await ws.send(json.dumps(msg_body))

    danmaku = asyncio.create_task(live_danmaku.connect())
    # 用来检查bot是否运行的命令

    async def group_message_handler():
        while True:
            messages = json.loads(await ws.recv())
            if messages['type'] == 'GroupMessage' and messages['sender']['group']['id'] in GROUPS and messages['messageChain'][1]['text'] == '/botStatus':
                data_body = {
                    'sessionKey': bot_data['session'],
                    'target': messages['sender']['group']['id'],
                    'messageChain': [{'type': 'Plain', 'text': TEXT}]
                }
                msg_body = {
                    'syncId': 'sendGroupMessage',
                    'command': 'sendGroupMessage',
                    'subCommand': None,
                    'content': data_body
                }
                await ws.send(json.dumps(msg_body))
            await asyncio.sleep(0.5)

    msg_task = asyncio.create_task(group_message_handler())
    await danmaku
    await msg_task

if __name__ == '__main__':
    asyncio.run(main())
