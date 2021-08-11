from requests import post
from websockets import client
from bilibili_api.live import LiveDanmaku
import json
import api
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
    mriai = post(API_URL+api.AUTH, json={'authKey': AUTH}).json()
    if mriai['code'] == 0:
        # 保存 session
        bot_data['session'] = mriai['session']
        post(API_URL+api.BIND,
             json={'sessionKey': bot_data['session'], 'qq': QQ})
        print('Auth succeed')
    else:
        print('Auth failed')
        return
    # 开一个 websocket，保持 session
    ws_server = API_URL.replace('http', 'ws')
    ws = await client.connect(ws_server + '/message?sessionKey=' + bot_data['session'])
    # 连接弹幕服务器
    live_danmaku = LiveDanmaku(config['room_id'],max_retry=5000)

    @live_danmaku.on('LIVE')
    async def live(arg):
        for v in GROUPS:
            msg_body = {
                "sessionKey": bot_data['session'],
                "target": v,
                "messageChain": [{"type": "Plain", "text": TEXT}]
            }
            post(API_URL+api.POST_MESSAGE,json=msg_body)
    
    danmaku = asyncio.create_task(live_danmaku.connect())
    # 用来检查bot是否运行的命令
    async def group_message_handler():
        while True:
            messages = json.loads(await ws.recv())
            if messages['type'] == 'GroupMessage' and messages['sender']['group']['id'] in GROUPS and messages['messageChain'][1]['text'] == '/botStatus':
                msg_body = {
                "sessionKey": bot_data['session'],
                "target": messages['sender']['group']['id'],
                "messageChain": [{"type": "Plain", "text": "开播通知bot正在运行"}]
                }
                post(API_URL+api.POST_MESSAGE,json=msg_body)
            await asyncio.sleep(0.5)

    msg_task = asyncio.create_task(group_message_handler())
    await danmaku
    await msg_task

if __name__ == '__main__':
    asyncio.run(main())
