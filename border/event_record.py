import requests as req
from pyquery import PyQuery as Pq
import time
import json

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
    if response.status_code == 200:
        obj = json.loads(response.text)
        latest_border = obj['data']['logs'][-1]
        with open(cache_path, "w") as cache_file:
            json.dump(latest_border, cache_file)
    else:
        raise IOError(f"Error {response.status_code}")
