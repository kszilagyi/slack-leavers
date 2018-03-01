import argparse
from slackclient import SlackClient
from time import time
from datetime import datetime

parser = argparse.ArgumentParser(description='Lists people who has left a slack channel')

parser.add_argument('--from-month-ago', type=int, required=True,
                    help='start from this number of months ago')

parser.add_argument('--to-month-ago', type=int, required=True,
                    help='until to this number of months ago')

parser.add_argument('--slack-token', type=str, required=True,
                    help='slack token')

parser.add_argument('channel', type=str, help='Name of the channel without #')

args = parser.parse_args()
from_month_ago = args.from_month_ago
to_month_ago = args.to_month_ago
slack_token = args.slack_token
channel_name = args.channel

assert from_month_ago > to_month_ago, "From-month-ago should be bigger (earlier) than to-month-ago."

sc = SlackClient(slack_token)

x = '%s' % channel_name
print(x)

channel_id = next(
    (channel['id'] for channel in sc.api_call("channels.list")['channels'] if channel['name'] == channel_name), None)
if channel_id is None:
    print('channel not found')
    exit(1)

print("Channel id is %s" % channel_id)
# todo this API is paged but we only do the first page.
# It should be OK for low volume channels if the interval is not too high
all_events = sc.api_call("channels.history",
                         channel=channel_id,
                         count=1000)
only_leaves = []
for event in all_events['messages']:
    if 'subtype' in event and event['subtype'] == 'channel_leave':
        only_leaves.append(event)

rude_month_timestamp = 60 * 60 * 24 * 30

from_timestamp = time() - from_month_ago * rude_month_timestamp
to_timestamp = time() - to_month_ago * rude_month_timestamp

print("from: %s" % datetime.fromtimestamp(from_timestamp))
print("to: %s" % datetime.fromtimestamp(to_timestamp))

only_leaves_in_period = set(
    [leave['user'] for leave in only_leaves if from_timestamp < float(leave['ts']) < to_timestamp])

# todo this doesn't work if the number of people is bigger than 100
current_members = set(sc.api_call('conversations.members',
                                  channel=channel_id)['members'])
left_and_didnt_come_back = only_leaves_in_period - current_members

resolved_left_and_didnt_come_back = [sc.api_call("users.info",
                                                 user=user)['user'] for user in left_and_didnt_come_back]

without_deleted = [user['profile']['email'] for user in resolved_left_and_didnt_come_back if not user['deleted']]

print(without_deleted)
