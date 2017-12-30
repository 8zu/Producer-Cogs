import datetime
import json
import time
import threading
import border.event_record as er
from discord.ext import commands
from pyquery import PyQuery as Pq


class Border:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def mlborder(self, event_code: int = None):
        # Catch current ranking points. Need event code.
        if event_code is not None:
            url = "http://mlborder.com/events/{}/".format(event_code)
            document = Pq(url)
            title = document('title').text()
            body = document('body')
            border_div = Pq(body('.tab-pane')[0])('div')
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
            now = (datetime.datetime.fromtimestamp(current_timestamp) + datetime.timedelta(hours=1)).strftime(
                '%Y/%m/%d %H:%M:%S')
            borders = {int(k): v for k, v in border_summary['borders'].items()}

            msg = '\n'.join(
                [f"{event_name}\n{event_info}\n{left_or_passed_time}\n\n{now}{self.pretty_print_border(borders)}"]
            )

            await self.bot.say(msg)
        else:
            await self.bot.say("mlborder need an event code.")

    @commands.command()
    async def mltdborder(self, event_code: int = None):
        if event_code is not None:
            global e_code
            e_code = event_code
            global t
            t = threading.Timer(900, er.fetch_latest_event_border(e_code))
            if t.isAlive:
                t.cancel()
                t = threading.Timer(900, er.fetch_latest_event_border(e_code))
                t.start()
            else:
                t.start()
        msg = er.get_latest_event_data(e_code).__repr__().join('\n')
        with open(er.cache_path, "r") as cache:
            for line in cache.buffer:
                msg.join(line.__repr__() + '\n')
        await self.bot.say(msg)

    @staticmethod
    def pretty_print_border(borders):
        max_len = len(str(max(borders))) + 8 + len('{:,}'.format(max(borders.values())))
        lines = ['```']
        for n, data in sorted(borders.items()):
            offset = len(str(n)) + 8
            lines.append(f"{n}位：  {data:>{max_len-offset},}")
        lines.append('```')
        return lines


def setup(bot):
    bot.add_cog(Border(bot))
