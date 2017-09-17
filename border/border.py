import asyncio
import datetime
import json
import time

import aiohttp
import discord
from discord.ext import commands
from pyquery import PyQuery as pq

class Border:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def mlborder(self, event_code: int = None):
        # Catch current ranking points. Need event code.
        if event_code is not None:
            url = "http://mlborder.com/events/{}/".format(event_code)
            document = pq(url)
            title = document('title').text()
            body = document('body')
            border_div = pq(body('.tab-pane')[0])('div')
            data_react_props = border_div.html()

            original_data = data_react_props[data_react_props.index('{'):data_react_props.rindex('}') + 1]
            prepare_json = original_data.replace('&quot;', '"')
            json_data = json.loads(prepare_json)

            event_name = title[title.index('『') + 1:title.rindex('』')]
            event_info = document('.list-group-item').text()

            ending_time = event_info[event_info.index('〜') + 1:event_info.rindex(',')]
            ending_timestamp = time.mktime(time.strptime(ending_time, '%Y/%m/%d %H:%M'))
            current_timestamp = time.time()
            left_or_passed_time = ''
            if current_timestamp < ending_timestamp:
                left_timestamp = ending_timestamp - current_timestamp
                left_or_passed_time += 'あと　'
                left_or_passed_time += time.strftime('%d', time.localtime(left_timestamp))
                left_or_passed_time += '日'
                left_or_passed_time += time.strftime('%H:%M:%S', time.localtime(left_timestamp))
            else:
                pass_timestamp = current_timestamp - ending_timestamp
                left_or_passed_time += time.strftime('%d', time.localtime(pass_timestamp))
                left_or_passed_time += '日'
                left_or_passed_time += time.strftime('%H:%M:%S', time.localtime(pass_timestamp))
                left_or_passed_time += '　過ごしだ'
            border_summary = json_data['border_summary']
            now = (datetime.datetime.fromtimestamp(current_timestamp) + datetime.timedelta(hours=1)).strftime('%Y/%m/%d %H:%M:%S')
            borders = border_summary['borders']

            msg = '\n'.join([f'{event_name}\n{event_info}\n{left_or_passed_time}\n\n{now}',
                             f"1位：\t\t{borders['1']:,}",
                             f"10位：\t\t{borders['10']:,}",
                             f"100位：\t\t{borders['100']:,}",
                             f"500位：\t\t{borders['500']:,}",
                             f"1200位：\t\t{borders['1200']:,}",
                             f"1300位：\t\t{borders['1300']:,}"])

            await self.bot.say(msg)
        else:
            await self.bot.say("mlborder need an event code.")

def setup(bot):
    bot.add_cog(Border(bot))
