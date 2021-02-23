import requests, config
from vk_messages import MessagesAPI


def SortAnswer(answer):
    number_of_message = []
    messages = []
    new_pts = answer['new_pts']
    for i in range(len(answer['history'])):
        if (answer['history'][i][0] == 4 or answer['history'][i][0] == 7) and (answer['messages']['items'][i]['from_id'] != 272493558):
            print('зашли в функцию')
            number_of_message += [i]
    for i in number_of_message:
        first_last_name = answer['profiles'][i]['first_name']+' '+answer['profiles'][i]['last_name']
        message = answer['messages']['items'][i]
        from_id = message['from_id']
        if len(message['text']) > 0:
            text = message['text']
        else:
            text = ''
        if message['attachments'] != None:
            attachments = SortAttachment(message['attachments'])
        else:
            attachments = None
        messages.append(dict(from_id= from_id, text= text, attachments= attachments, name= first_last_name))
    return messages, new_pts



def SortAttachment(attachments):
    filenames = {'photo': [], 'voice': []}
    for attachment in attachments:
        if attachment['type'] == 'photo':
            id = attachment['photo']['id']
            url = attachment['photo']['sizes'][-1]['url']
            photo = requests.get(url)
            filename = 'cash/{}'.format(id)+'.jpeg'
            with open(filename, 'wb') as file:
                file.write(photo.content)
            filenames['photo'] += [filename]
        elif attachment['type'] == 'video':
            id = attachment['video']['id']
            image_url = attachment['video']['image']['url']
            photo = requests.get(image_url)
            filename = 'cash/{}'.format(id) + '.jpeg'
            with open(filename, 'wb') as file:
                file.write(photo.content)
            filenames['photo'] += [filename]
        elif attachment['type'] == 'audio_message':
            id = attachment['audio_message']['id']
            url = attachment['audio_message']['link_ogg']
            audio_message = requests.get(url)
            filename = 'cash/{}'.format(id) + '.ogg'
            with open(filename, 'wb') as fd:
                fd.write(audio_message.content)
            filenames['voice'] += [filename]
        return filenames


class VKbot(MessagesAPI):
    def __init__(self, login, password, two_factor, cookies_save_path):
        MessagesAPI.__init__(self, login, password,two_factor,cookies_save_path)


    def getLongPollServer(self):
        """gets server, severet key of connction
        actual ts and pts to communicate with LongPollHistory"""
        response = self.method('messages.getLongPollServer',need_pts=1, lp_version=3, v=5.130)
        return response['server'], response['key'], response['ts'], response['pts']


    def getLongPollHistory(self, ts, pts):
        try:
            answer = self.method('messages.getLongPollHistory', ts=ts, pts=pts)
        except Exception:
            server, key, ts, pts = self.getLongPollServer()
            return self.getLongPollHistory(ts, pts)
        return answer


    def IsMessagesToMe(self, response):
        if len(response['updates']) > 0:
            for i in range(len(response['updates'])):
                if response['updates'][i][0] == 4:
                    return True
        return False


    def LongPolling(self, telegrambot, mode=32, wait=25):
        try:
            while True:
                server, key, ts, pts = self.getLongPollServer()
                api = 'https://{0}?act=a_check&key={1}&ts={2}&wait={5}&mode={3}&version=2&pts={4}'.format(server, key, ts, mode, pts,wait)
                response = requests.get(api).json()
                if 'failed' in response:
                    continue
                else:
                    if self.IsMessagesToMe(response):
                        answer = self.getLongPollHistory(ts,pts)
                        print(answer)
                        answer, pts = SortAnswer(answer)
                        print(answer) # anser= [{'from_id': from_id, 'text': text, 'attachments'= {'photo': [], 'voice': []}, 'name': 'Lastname Firstname'}]
                        for message in answer:
                            from_id = str(message['from_id'])
                            if from_id in config.chat:
                                chat_id = config.chat[from_id]['telegram_chat']
                                print('chat_id is there')
                            else:
                                print('chat id isnt there')
                                continue
                            if (len(message['text']) > 0):
                                telegrambot.send_message(chat_id, message['text'])
                            if message['attachments'] != None:
                                if len(message['attachments']['photo']) > 0:
                                    for file in message['attachments']['photo']:
                                        with open(file, 'rb') as filetoread:
                                            telegrambot.send_photo(chat_id, filetoread, None)
                                if len(message['attachments']['voice']) > 0:
                                    for file in message['attachments']['voice']:
                                        with open(file, 'rb') as filetoread:
                                            telegrambot.send_voice(chat_id, filetoread, None)
        except Exception:
            self.LongPolling(telegrambot, mode, wait)