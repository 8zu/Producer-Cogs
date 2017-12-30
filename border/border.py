import datetime
import json
import threading
import time

import requests as req
from discord.ext import commands
from pyquery import PyQuery as Pq

# [theater-gate] website url
event_url = "https://days.765prolive.theater/event/"

# border data api url without defined event code
json_api_url = "https://otomestorm.anzu.work/events/{}/rankings/event_point"

# cache path
cache_path = "cache/current.json"


class EventRecord(object):
    def __init__(self, event_code, name, starts, ends):
        self.id = int(event_code)
        self.name = name
        self.format_string = "%Y-%m-%dT%H:%M:%S"
        self.starts = time.strptime(starts, self.format_string)
        self.ends = time.strptime(ends, self.format_string)

    def __repr__(self):
        starts = time.strftime(self.format_string, self.starts)
        ends = time.strftime(self.format_string, self.ends)
        return f"Event #{self.id}: {self.name}\nstarts {starts}\nends {ends}"


def get_latest_event_data(event_code):
    """
    Accept an event code to pick out the correct record info.
    :param event_code: MLTD event code
    :return: packaged event info including event title, start time and end time.
    """
    response = req.get(event_url)
    if response.status_code == 200:
        html = Pq(response.text)
        event_table = Pq(html("#event"))
        latest_tr = event_table("tr")
        # by using iterator to pick out correct record
        for tr in latest_tr:
            # skip the first tr and the last one, which been included in <thead> and <tfoot>
            if Pq(tr[0]).text() == "Name":
                continue
            else:
                link = Pq(tr[0]).children()[0]
                code = link.attrib['href'].split("/")[-1]
                if code == event_code.__str__():
                    args = list(map(lambda td: td.text_content(), tr))
                    return EventRecord(code, *args)
    else:
        raise IOError(f"Error {response.status_code}")


def fetch_latest_event_border(event_code):
    """
    Fetch the latest event border and write into a "cache" file :D
    :param event_code: MLTD event code
    :return: no function return
    """
    actual_api_url = json_api_url.format(event_code)
    response = req.get(actual_api_url)
    obj = json.loads(response.text)
    latest_border = obj['data']['logs'][-1]
    with open(cache_path, "w") as cache_file:
        json.dump(latest_border, cache_file)


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

            msg = '\n'.join([f'{event_name}\n{event_info}\n{left_or_passed_time}\n\n{now}'] + \
                            self.pretty_print_border(borders))

            await self.bot.say(msg)
        else:
            await self.bot.say("mlborder need an event code.")

    @commands.command()
    async def mltdborder(self, event_code: int = None):
        if event_code is not None:
            global e_code
            e_code = event_code
            global t
            t = threading.Timer(900, fetch_latest_event_border(e_code))
            if t.isAlive:
                t.cancel()
                t = threading.Timer(900, fetch_latest_event_border(e_code))
                t.start()
            else:
                t.start()
        msg = get_latest_event_data(e_code).__repr__().join('\n')
        with open(cache_path, "r") as cache:
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
