#!/usr/bin/python
# -*- coding: utf-8 -*-
# Standard modules
from argparse import ArgumentParser
import csv
from datetime import datetime
import sys
# Third-party modules
import dns.resolver
import requests
from termcolor import colored


BOLD = '\033[1m'
ENDBOLD = '\033[0m'


class NoValidApiKeyException(Exception):
    pass


def query_api_keys(api_keys):
    """Get info about API keys usage"""
    if not api_keys:
        print(colored(BOLD + 'No API keys loaded.' + ENDBOLD, 'red'))
    for api_key in api_keys:
        url = 'https://api.hunter.io/v2/account?api_key={0}'.format(api_key)
        response = requests.request('GET', url)
        if 'errors' in response.json():
            err_msg = 'API key: "{0}". Error: {1}'.format(api_key, response.json()['errors'][0]['details'])
            print(colored(BOLD + err_msg + ENDBOLD, 'red'))
            continue
        else:
            account_info = response.json()['data']
            print account_info
            calls_left = account_info['calls']['available'] - account_info['calls']['used']
            if calls_left <= 0:
                print(colored(BOLD + '{0} API calls left for {1} API key.'.format(calls_left, api_key) + ENDBOLD, 'yellow'))
                print(colored(BOLD + 'Date of API reset: {0}\n'.format(account_info['reset_date']) + ENDBOLD, 'yellow'))
                continue
            else:
                print(colored(BOLD + '{0} API calls left ({1} emails max) for  API key: {2}.'.format(calls_left, calls_left*10, api_key) + ENDBOLD, 'green'))


def get_api_key(email_count, api_keys):
    """Get API key and count of email to query"""
    if not api_keys:
        print(colored('No API keys defined, quitting now', 'red'))
        sys.exit(0)
    for api_key in api_keys:
        url = 'https://api.hunter.io/v2/account?api_key={0}'.format(api_key)
        response = requests.request('GET', url)
        if 'errors' in response.json():
            err_msg = 'API key: "{0}". Error: {1}'.format(api_key, response.json()['errors'][0]['details'])
            print(colored(BOLD + err_msg + ENDBOLD, 'red'))
        else:
            account_info = response.json()['data']
            requests_left = account_info['calls']['available'] - account_info['calls']['used']
            #print requests_left
            if requests_left <= 0:
                continue
            elif requests_left * 10 >= email_count:
                return api_key, email_count
            else:
                return api_key, requests_left * 10
    raise NoValidApiKeyException("No valid API keys")


def check_MX(domain):
    """Returns list of domains with MX record"""
    resolver = dns.resolver.Resolver()
    resolver.timeout = 5
    resolver.lifetime = 5
    try:
        resolver.query(domain, 'mx')
        return True
    except:
        return False


def query_domain(domain, email_count, api_keys):
    """Query hunter.io for domain emails"""
    emails = []
    offset = 0
    emails_left = email_count
    while emails_left > 0:
        #print emails_left
        try:
            api_key, email_request_count = get_api_key(emails_left, api_keys)
        except NoValidApiKeyException:
            raise NoValidApiKeyException
        if api_key is not None:
            limit = email_request_count
            # print('Limit: {}, API: {}'.format(limit, api_key))
            url = 'https://api.hunter.io/v2/domain-search?domain={0}&api_key={1}&limit={2}&offset={3}'.format(domain, api_key, limit, offset)
            response = requests.request('GET', url)
            data = response.json()
            #if 'data' not in data:
                #print data
            #print data['data']
            for email in data['data']['emails']:
                emails.append(email['value'])
        #print emails
        #print len(data['data']['emails'])
        offset += len(data['data']['emails'])
        emails_left -= len(data['data']['emails'])
    return emails


def query_email_count(domain):
    """Queries hunter.io and returns emails count for domain"""
    url = 'https://api.hunter.io/v2/email-count?domain={0}'.format(domain)
    response = requests.request('GET', url)
    email_count = response.json()['data']['total']
    return email_count


def save_results(results, input_filename):
    """Save emails into CSV file"""
    filename = input_filename.split('.')[0] + '_results.csv'
    with open(filename, 'wb') as outfile:
        csvfields = ['Domain', 'Email']
        csvwriter = csv.DictWriter(outfile, csvfields, restval=None, delimiter=';')
        csvwriter.writeheader()
        for result in results:
            for email in result['emails']:
                row = {'Domain': result['domain'], 'Email': email}
                csvwriter.writerow(row)
    print(colored(BOLD + 'All emails are saved into {} file!'.format(filename) + ENDBOLD, 'green'))


def main():
    results = []
    parser = ArgumentParser('Search emails via hunter.io using multiple API keys')
    parser.add_argument('filename', nargs='?', help='File containing domain names')
    parser.add_argument('-a', '--apikey', action='store_true', help='Show API key information')

    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(0)

    # Load API keys
    with open('api.txt', 'r') as api_file:
        api_keys = [k.strip().split(':')[1] for k in api_file.readlines()]

    if args.apikey:
        query_api_keys(api_keys)
        sys.exit(0)

    with open(args.filename, 'rb') as infile:
        domains = [line.strip() for line in infile.readlines()]
        for domain in domains:
            print(colored(BOLD + 'Domain: {}'.format(domain) + ENDBOLD, 'white'))
            sys.stdout.write(colored('Getting emails count: ', 'cyan'))
            email_count = query_email_count(domain)
            sys.stdout.write(colored('{}\n'.format(email_count), 'green'))
            if email_count:
                print(colored('Getting emails: ', 'cyan'))
                try:
                    emails = query_domain(domain, email_count, api_keys)
                except NoValidApiKeyException:
                    print(colored(BOLD + 'No valid API keys' + ENDBOLD, 'red'))
                    continue
                for email in emails:
                    print(colored(BOLD + email + ENDBOLD, 'yellow'))
                result = {'domain': domain, 'emails': emails}
                results.append(result)
            print
    save_results(results, args.filename)

if __name__ == '__main__':
    main()
