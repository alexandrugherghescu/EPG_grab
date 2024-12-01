#!/usr/bin/python
import re
import argparse
import json
import os

import requests
from requests.exceptions import HTTPError
from requests.exceptions import ConnectionError

from datetime import datetime, timedelta

import json

HOW_MANY_DAYS_TO_GRAB = 4
WEEK_DAYS = ('luni', 'marti', 'miercuri', 'joi', 'vineri', 'sambata', 'duminica')
dict_categories_conversion = {'Ştiri': 'News', 'Divertisment': 'Variety show', 'Diverse': 'yes', 'Film': 'Movie', 'Acţiune': 'Action', 'SF': 'Science fiction', 'Aventuri': 'Adventure', 'Dramă': 'Drama', 'Fantastic': 'Fantasy', 'Război': 'War', 'Thriller': 'Thriller', 'Crimă': 'Crime', 'Comedie': 'Comedy', 'Romantic': 'Romance', 'Dragoste': 'Love', 'Familie': 'Family', 'Istoric': 'Historical movie'}
#dic_channels_temp = dict([])

def escape_xmltv_chars(xmltv_field):
    #"   &quot;
    #'   &apos;
    #<   &lt;
    #>   &gt;
    #&   &amp;
    str_xmltv_field = xmltv_field.strip()
    #str_xmltv_field = str_xmltv_field.replace('"', r'\"')
    str_xmltv_field = str_xmltv_field.replace('"', r'”')

    str_xmltv_field = str_xmltv_field.replace('\'', r'_')
    str_xmltv_field = str_xmltv_field.replace('<', r'_')
    str_xmltv_field = str_xmltv_field.replace('>', r'_')
    str_xmltv_field = str_xmltv_field.replace('&', r'and')
    #str_xmltv_field = str_xmltv_field.replace('\n', r'_')
    str_xmltv_field = str_xmltv_field.replace('\t', r'_')
    return str_xmltv_field


def assembly_program(str_channels_name, obj_row):
    #  <programme start="20080715003000 -0600" stop="20080715010000 -0600" channel="I10436.labs.zap2it.com">
    #    <title lang="ro">TITLE</title>
    #    <desc lang="ro">DESCRIPTION</desc>
    #    <category lang="ro">Diverse</category>
    #  </programme>
    # expected: {'id': '1033642257', 'start': '2023-12-31T07:00:00+02:00', 'stop': '2023-12-31T07:59:59+02:00', 'stationId': '559', 'replay': False, 'live': False, 'online': True, 'OTTRights': True, 'categories': ['Diverse'], 'title': 'Dimineata facem piața', 'desc': '', 'templating': []}
    str_output = ''
    #str_pattern_event = '\n\n(\w{2}).(\w{2}).(\w{4})\n\t\t\t(.*?):(.*?)-(.*?):(.*?)\n\n\t\n\t\t\t(.*?)\n\n'
    str_start_in = obj_row['start']
    str_stop_in = obj_row['stop']
    str_pattern_time = '(\w{4})-(\w{2})-(\w{2})T(\w{2}):(\w{2}):(\w{2})\+02:00'
    obj_start_in = re.search(str_pattern_time, str_start_in)
    obj_stop_in = re.search(str_pattern_time, str_stop_in)
    if obj_start_in and obj_stop_in:
        # verify date
        if obj_start_in.lastindex == 6 and obj_stop_in.lastindex == 6:
            str_year = obj_start_in.group(1)
            str_month = obj_start_in.group(2)
            str_day = obj_start_in.group(3)
            str_start_hour = obj_start_in.group(4).strip()
            str_start_minute = obj_start_in.group(5).strip()
            str_start_second = obj_start_in.group(6).strip()
            int_day = int(str_day)
            int_month = int(str_month)
            int_year = int(str_year)
            int_hour = int(str_start_hour)
            int_minute = int(str_start_minute)
            int_second = int(str_start_second)
            obj_start_out = str(int_year).zfill(4) + str(int_month).zfill(2) + str(int_day).zfill(2) + str(int_hour).zfill(2) + str(int_minute).zfill(2) + str(int_second).zfill(2)
            str_year = obj_stop_in.group(1)
            str_month = obj_stop_in.group(2)
            str_day = obj_stop_in.group(3)
            str_start_hour = obj_stop_in.group(4).strip()
            str_start_minute = obj_stop_in.group(5).strip()
            str_start_second = obj_stop_in.group(6).strip()
            int_day = int(str_day)
            int_month = int(str_month)
            int_year = int(str_year)
            int_hour = int(str_start_hour)
            int_minute = int(str_start_minute)
            int_second = int(str_start_second)
            obj_stop_out = str(int_year).zfill(4) + str(int_month).zfill(2) + str(int_day).zfill(2) + str(int_hour).zfill(2) + str(int_minute).zfill(2) + str(int_second).zfill(2)
            str_output = '  <programme start=\"' + obj_start_out + ' +0200\" stop=\"' + obj_stop_out + ' +0200\" channel=\"' + str_channels_name + '\">\r\n'

            # {'id': '1048398813', 'start': '2024-01-03T06:00:00+02:00', 'stop': '2024-01-03T06:59:59+02:00', 'stationId': '459', 'replay': False, 'live': False, 'online': True, 'OTTRights': True, 'categories': ['Muzică'], 'title': 'Eat, Sleep, ZU, Repeat', 'desc': '', 'templating': [], 'tvShowId': '16743', 'obs': '', 'subTitle': 'Veronica se întoarce', 'movieId': '4904', 'movieImdbRating': '7.50', 'movieCinemagiaRating': '8.55', 'date': '2001', 'country': ['SUA'], 'titleOriginal': 'Smallville', 'credits': {'director': ['Alfred Gough', 'Turi Meyer', 'Tim Scanlan'], 'actor': ['Jensen Ackles', 'Kelly Brook', 'Erica Durance']}, 'url': 'https://www.cinemagia.ro/filme/smallville-4904/', 'icon': 'https://www.programetv.ro/img/shows/82/5f/hallo-deutschland.jpg?key=Z2lfZnVial90cmFyZXZwLzAxLzQ5LzgzLzM1MTM5NnktMTIwazE3MC1hLW4wNDk3b242LndjdA==', 'rating': 'ap12', 'season': '3', 'episode': '3'}
            #print('##########################################################')
            #print(obj_row)
            #print('##########################################################')
            #for key, value in obj_row.items():
            #    dic_channels_temp[key] = value

            # 'title': 'Eat, Sleep, ZU, Repeat'
            if 'title' in obj_row:
                str_output = str_output + '    <title lang="ro">' + escape_xmltv_chars(obj_row['title']) + '</title>\r\n'
            # 'subTitle': 'Veronica se întoarce'
            if 'subTitle' in obj_row:
                str_output = str_output + '    <sub-title lang="ro">' + escape_xmltv_chars(obj_row['subTitle']) + '</sub-title>\r\n'
            # 'categories': ['Muzică']
            if 'categories' in obj_row:
                for items in obj_row['categories']:
                    str_output = str_output + '    <category lang="ro">' + escape_xmltv_chars(items) + '</category>\r\n'
                    if items in dict_categories_conversion:
                        str_output = str_output + '    <category lang="en">' + escape_xmltv_chars(dict_categories_conversion[items]) + '</category>\r\n'
            # 'desc': ''
            if 'desc' in obj_row:
                str_output = str_output + '    <desc lang="ro">' + escape_xmltv_chars(obj_row['desc']) + '</desc>\r\n'
            # 'movieImdbRating': '7.50'
            if 'movieImdbRating' in obj_row:
                # <star-rating>
                # <value>6.1/10</value>
                # </star-rating>
                str_output = str_output + '    <star-rating>\r\n'
                str_output = str_output + '      <value>' + escape_xmltv_chars(obj_row['movieImdbRating']) + '/10</value>\r\n'
                str_output = str_output + '    </star-rating>\r\n'
            else:
                # 'movieCinemagiaRating': '8.55'
                if 'movieCinemagiaRating' in obj_row:
                    # <star-rating>
                    # <value>6.1/10</value>
                    # </star-rating>
                    str_output = str_output + '    <star-rating>\r\n'
                    str_output = str_output + '      <value>' + escape_xmltv_chars(obj_row['movieCinemagiaRating']) + '/10</value>\r\n'
                    str_output = str_output + '    </star-rating>\r\n'
            # 'date': '2001'
            if 'date' in obj_row:
                str_output = str_output + '    <date>' + escape_xmltv_chars(obj_row['date']) + '</date>\r\n'
            # 'country': ['SUA']
            if 'country' in obj_row:
                for items in obj_row['country']:
                    str_output = str_output + '    <country lang="ro">' + escape_xmltv_chars(items) + '</country>\r\n'
            # 'titleOriginal': 'Smallville'
            if 'titleOriginal' in obj_row:
                str_output = str_output + '    <title lang="en">' + escape_xmltv_chars(obj_row['titleOriginal']) + '</title>\r\n'
            # 'credits': {'director': ['Alfred Gough', 'Turi Meyer', 'Tim Scanlan'], 'actor': ['Jensen Ackles', 'Kelly Brook', 'Erica Durance']}
            if 'credits' in obj_row:
                #<credits>
                #<director>{Name}</director>
                #<actor>{Name}</actor>
                #<guest>{Name}</guest>
                #</credits>
                #<writer>Seth MacFarlane</writer>
                obj_credits = obj_row['credits']
                # separate director from actor
                str_output_temp = ''
                if 'director' in obj_credits:
                    for items in obj_credits['director']:
                        str_output_temp = str_output_temp + '      <director>' + escape_xmltv_chars(items) + '</director>\r\n'
                if 'actor' in obj_credits:
                    for items in obj_credits['actor']:
                        str_output_temp = str_output_temp + '      <actor>' + escape_xmltv_chars(items) + '</actor>\r\n'
                if len(str_output_temp) > 2:
                    str_output = str_output + '    <credits>\r\n'
                    str_output = str_output + str_output_temp
                    str_output = str_output + '    </credits>\r\n'
            # 'icon': 'https://www.programetv.ro/img/shows/82/5f/hallo-deutschland.jpg?key=Z2lfZnVial90cmFyZXZwLzAxLzQ5LzgzLzM1MTM5NnktMTIwazE3MC1hLW4wNDk3b242LndjdA=='
            if 'icon' in obj_row:
                str_output = str_output + '    <icon src="' + escape_xmltv_chars(obj_row['icon']) + '"/>\r\n'
            # 'rating': 'ap12'
            #<rating system="RO">
            #<value>12</value>
            #</rating>
            if 'rating' in obj_row:
                str_output = str_output + '    <rating system="RO">\r\n'
                str_output = str_output + '      <value>' + escape_xmltv_chars(obj_row['rating']) + '</value>\r\n'
                str_output = str_output + '    </rating>\r\n'
            # 'season': '3', 'episode': '3'
            #<episode-num system="xmltv_ns">0.8.</episode-num>
            if 'season' in obj_row and 'episode' in obj_row:
                str_season = obj_row['season']
                str_episode = obj_row['episode']
                if str_season.isdigit() and  str_episode.isdigit():
                    int_season = int(str_season)
                    int_episode = int(str_episode)
                    int_season = int_season - 1
                    int_episode = int_episode - 1
                    str_output = str_output + '    <episode-num system="xmltv_ns">' + str(int_season) + '.' + str(int_episode) + '.</episode-num>>\r\n'
            str_output = str_output + '  </programme>\r\n'
            return str_output
    return ''


def grab_one_day(str_channel, str_channels_name, bln_is_today, str_week_day):
    if bln_is_today:
        # https://www.programetv.ro/post/24-mix-teleshop/
        str_link = 'https://www.programetv.ro/post/' + str_channel + '/'
    else:
        # https://www.programetv.ro/post/24-mix-teleshop/luni/
        str_link = 'https://www.programetv.ro/post/' + str_channel + '/' + str_week_day + '/'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    str_output = ''
    try:
        # request page
        response = requests.get(str_link, headers=headers)
        # If the response was successful, no Exception will be raised
        response.raise_for_status()
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')
    except ConnectionError as ce:
        print(ce)
    else:
        #print('Success!')
        response.encoding = 'utf-8'  # Optional: requests infers this internally
        str_web_page = response.text
        obj_extr_1 = re.search(r'var pageData = (\{.*?\});', str_web_page)
        if obj_extr_1:
            str_extract_1 = obj_extr_1.group(1)
            data = json.loads(str_extract_1)
            for row in data['shows']:
                str_output = str_output + assembly_program(str_channels_name, row)
    return str_output


def grab_one_channel(str_channel, str_channels_name):
    int_epg_for_n_days = HOW_MANY_DAYS_TO_GRAB
    dat_today = datetime.now()
    str_output = ''
    for int_days_forward in range(int_epg_for_n_days):
        if int_days_forward == 0:
            bln_today = True
        else:
            bln_today = False
        dat_date = dat_today + timedelta(int_days_forward)
        int_week_day = dat_date.weekday()
        str_output = str_output + grab_one_day(str_channel, str_channels_name, bln_today, WEEK_DAYS[int_week_day])
    return str_output


def generate_channels(dict_channels):
    str_output = ''
    for key, value in dict_channels.items():
        str_output = str_output + '  <channel id="' + value[0] + '">\r\n'
        str_output = str_output + '    <display-name>' + key + '</display-name>\r\n'
        str_output = str_output + '    <icon src="' + value[1] + '" />\r\n'
        str_output = str_output + '  </channel>\r\n'
    return str_output


def grab_epg(dict_channels):
    # write header
    str_output = '<?xml version="1.0" encoding="UTF-8"?>\r\n'
    str_output = str_output + '<tv generator-info-name="EPGWebGrab from https://www.programetv.ro" generator-info-url="***">\r\n'
    # Phase 1: generate the channels section
    str_output = str_output + generate_channels(dict_channels)
    # Phase 2: grab channel content
    for key, value in dict_channels.items():
        print('grab: ' + str(key))
        str_output = str_output + grab_one_channel(value[0], key)
    # write end
    str_output = str_output + '</tv>'
    return str_output


def channels_dump(str_ch_file_path):
    str_link = 'https://www.programetv.ro/posturi-tv/toate/'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    try:
        # request page
        response = requests.get(str_link, headers=headers)
        # If the response was successful, no Exception will be raised
        response.raise_for_status()
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')
    except ConnectionError as ce:
        print(ce)
    else:
        #print('Success!')
        dict_channels = dict([])
        response.encoding = 'utf-8'
        str_web_page = response.text
        obj_extr_1 = re.search(r'var pageData = (\{.*?\});', str_web_page)
        if obj_extr_1:
            str_extract_1 = obj_extr_1.group(1)
            #print(str_extract_1)
            obj_json_data = json.loads(str_extract_1)
            for row in obj_json_data['stations']:
                str_display_name = escape_xmltv_chars(row['displayName'])
                dict_channels[str_display_name] = [row['slug'], row['icon']]
        #print(dict_channels)
        with open(str_ch_file_path, 'w') as out_file:
            json.dump(dict_channels, out_file, indent=4)
        return dict_channels


if __name__ == '__main__':
    print('ver.1.1.0')
    parser = argparse.ArgumentParser()
    parser.add_argument('file', nargs='?', default='/tmp')
    parser.add_argument('-cd', '--channels_dump', action='store_true', help='Dump channels parsed from site. Defaults to False.')
    parser.add_argument('-a', '--all_channels', action='store_true', help='Dump EPG for all channels. Defaults to False.')
    args = parser.parse_args()
    bln_channels_dump = args.channels_dump
    bln_all_channels = args.all_channels
    str_folder_path = args.file
    str_file_path = os.path.join(str_folder_path, 'guide.xml')
    str_ch_file_path = os.path.join(str_folder_path, 'ch.json')

    if bln_channels_dump:
        # Phase 1: dump channels
        dict_channels = channels_dump(str_ch_file_path)
    else:
        # Phase 2: load channels
        str_ch_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ch.json')
        with open(str_ch_file_path, 'r') as in_file:
            dict_channels = json.load(in_file)
        # if we have channels
        if bool(dict_channels):
            # Phase 3: grab EPG from www.programetv.ro
            str_output = grab_epg(dict_channels)
            # write file
            obj_file = open(str_file_path, "w", encoding="utf-8")
            obj_file.write(str_output)
            obj_file.close()