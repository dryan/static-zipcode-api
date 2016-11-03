#! /usr/bin/env python
from __future__ import unicode_literals

import csv
import json
import os
import re
import sys

import progressbar
from titlecase import titlecase


def get_csv_row_count(filename):
    # subtract 1 for the headers
    return sum(1 for line in open(filename, 'rU')) - 1


def dedupe_counties(counties):
    fips = []
    output = []
    for county in counties:
        if county['fips'] not in fips:
            output.append(county)
            fips.append(county['fips'])
    output.sort(key=lambda x: x['name'])
    return output

states = {}
states_verbose = {}
counties = {}
counties_verbose = {}
localities = {}
zip_coords = {}
zip_codes = {}

# process states
bar = progressbar.ProgressBar(widgets=['\033[92m', progressbar.FormatLabel('Processing States %(value)14s: '), progressbar.Percentage(
), ' ', progressbar.Bar(), ' ', progressbar.ETA(), '\033[0;0m'], maxval=get_csv_row_count('datasets/fips_states.csv')).start()
states_reader = csv.DictReader(open('datasets/fips_states.csv', 'rU'))
for row in states_reader:
    state_abbr = row.get('STUSAB')
    states[state_abbr] = {
        'fips': row.get('STATE').zfill(2),
        'abbr': state_abbr,
        'name': row.get('STATE_NAME'),
    }
    states_verbose[state_abbr] = {
        'fips': row.get('STATE').zfill(2),
        'abbr': state_abbr,
        'name': row.get('STATE_NAME'),
        'counties': 0,
        'postal_codes': 0,
        'localities': 0,
    }
    bar.update(bar.value + 1)
bar.finish()

# process counties
bar = progressbar.ProgressBar(widgets=['\033[92m', progressbar.FormatLabel('Processing Counties %(value)12s: '), progressbar.Percentage(
), ' ', progressbar.Bar(), ' ', progressbar.ETA(), '\033[0;0m'], maxval=get_csv_row_count('datasets/fips_counties.csv') + get_csv_row_count('datasets/fips_counties_2.csv')).start()
counties_reader = csv.DictReader(open('datasets/fips_counties_2.csv', 'rU'))
for row in counties_reader:
    county_fips = row.get('GEOID').zfill(5)
    counties[county_fips] = {
        'fips': county_fips[2:],
        'name': row.get('NAME'),
    }
    counties_verbose[county_fips] = {
        'fips': county_fips[2:],
        'name': row.get('NAME'),
        'localities': 0,
        'postal_codes': 0,
        'region': states[row.get('USPS')] if row.get('USPS') in states else {},
    }
    bar.update(bar.value + 1)
counties_reader = csv.DictReader(open('datasets/fips_counties.csv', 'rU'))
for row in counties_reader:
    county_fips = '{}{}'.format(row.get('STATEFP'), row.get('COUNTYFP'))
    if county_fips in counties:
        bar.update(bar.value + 1)
        continue
    counties[county_fips] = {
        'fips': county_fips[2:],
        'name': row.get('COUNTYNAME'),
    }
    counties_verbose[county_fips] = {
        'fips': county_fips[2:],
        'name': row.get('COUNTYNAME'),
        'localities': 0,
        'postal_codes': 0,
        'region': states[row.get('STATE')] if row.get('STATE') in states else {},
    }
    bar.update(bar.value + 1)
bar.finish()

# process zip codes
bar = progressbar.ProgressBar(widgets=['\033[92m', progressbar.FormatLabel('Processing ZIP Codes (1) %(value)7s: '), progressbar.Percentage(
), ' ', progressbar.Bar(), ' ', progressbar.ETA(), '\033[0;0m'], maxval=get_csv_row_count('datasets/zcta_zips.csv')).start()
zip_reader = csv.DictReader(open('datasets/zcta_zips.csv', 'rU'))
for row in zip_reader:
    zip_code = row.get('GEOID').zfill(5)
    zip_coords[zip_code] = {
        'lat': float(row.get('INTPTLAT')),
        'lng': float(row.get('INTPTLONG ')),
    }
    bar.update(bar.value + 1)
bar.finish()

bar = progressbar.ProgressBar(widgets=['\033[92m', progressbar.FormatLabel('Processing ZIP Codes (2) %(value)7s: '), progressbar.Percentage(
), ' ', progressbar.Bar(), ' ', progressbar.ETA(), '\033[0;0m'], maxval=get_csv_row_count('datasets/free_zipcode_database.csv')).start()
zip_reader = csv.DictReader(open('datasets/free_zipcode_database.csv', 'rU'))
for row in zip_reader:
    if row.get('State') not in states:
        # this is a territory we don't have data for
        bar.update(bar.value + 1)
        continue
    zip_code = row.get('Zipcode').zfill(5)
    if zip_code in zip_codes:
        zip_codes[zip_code]['localities'].append(
            row.get('LocationText')
        )
    else:
        zip_codes[zip_code] = {
            'postal_code': zip_code,
            'locality': row.get('LocationText'),
            'localities': [
                row.get('LocationText'),
            ],
            'region': states[row.get('State')],
            'lat': zip_coords[zip_code]['lat'] if zip_code in zip_coords else None,
            'lng': zip_coords[zip_code]['lng'] if zip_code in zip_coords else None,
            'type': row.get('ZipCodeType').replace(' ', ''),
            'counties': [],
        }
        states_verbose[row.get('State')]['postal_codes'] += 1
    states_verbose[row.get('State')]['localities'] += 1
    bar.update(bar.value + 1)
bar.finish()

bar = progressbar.ProgressBar(widgets=['\033[92m', progressbar.FormatLabel('Merging Counties %(value)15s: '), progressbar.Percentage(
), ' ', progressbar.Bar(), ' ', progressbar.ETA(), '\033[0;0m'], maxval=get_csv_row_count('datasets/zip_counties.csv')).start()
zip_reader = csv.DictReader(open('datasets/zip_counties.csv', 'rU'))
for row in zip_reader:
    zip_code = row.get('ZIP').zfill(5)
    if zip_code not in zip_codes:
        bar.update(bar.value + 1)
        continue
    zip_code_data = zip_codes[zip_code]
    zip_code_data['counties'].append(
        counties[row.get('COUNTY')]
    )
    states_verbose[zip_code_data['region']['abbr']]['counties'] += 1
    counties_verbose[row.get('COUNTY')]['postal_codes'] += 1
    bar.update(bar.value + 1)
bar.finish()

if not os.path.exists('no-callback/'):
    os.mkdir('no-callback')
if not os.path.exists('with-callback/'):
    os.mkdir('with-callback')

bar = progressbar.ProgressBar(widgets=['\033[92m', progressbar.FormatLabel('Outputting ZIP Code files %(value)6s: '), progressbar.Percentage(
), ' ', progressbar.Bar(), ' ', progressbar.ETA(), '\033[0;0m'], maxval=100000).start()
for i in xrange(0, 100000):
    zip_code = '{}'.format(i).zfill(5)
    zip_code_data = {}
    if zip_code in zip_codes:
        zip_code_data = zip_codes[zip_code]
        state_fips = zip_code_data['region']['fips']
        zip_code_data['counties'] = dedupe_counties(zip_code_data['counties'])
        zip_code_data['localities'] = list(set(zip_code_data['localities']))
        for county in zip_code_data['counties']:
            county_fips = '{}{}'.format(state_fips, county['fips'])
            if county_fips not in counties_verbose:
                continue
            counties_verbose[county_fips]['postal_codes'] += 1
            counties_verbose[county_fips][
                'localities'] += len(zip_code_data['localities'])
        for locality in zip_code_data['localities']:
            locality_full_name = '{}, {}'.format(
                locality, zip_code_data['region']['abbr'])
            if locality_full_name in localities:
                localities[locality_full_name]['postal_codes'].append(zip_code)
                localities[locality_full_name][
                    'counties'] += zip_code_data['counties']
            else:
                localities[locality_full_name] = {
                    'region': zip_code_data['region'],
                    'name': locality,
                    'postal_codes': [zip_code],
                    'counties': zip_code_data['counties'],
                }
    output = json.dumps(zip_code_data)
    no_callback = open('no-callback/{}.json'.format(zip_code), 'w')
    no_callback.write(output)
    no_callback.flush()
    no_callback.close()
    with_callback = open('with-callback/{}.json'.format(zip_code), 'w')
    with_callback.write('zipapicallback({});'.format(output))
    with_callback.flush()
    with_callback.close()
    bar.update(bar.value + 1)
bar.finish()

bar = progressbar.ProgressBar(widgets=['\033[92m', progressbar.FormatLabel('Outputting State files %(value)9s: '), progressbar.Percentage(
), ' ', progressbar.Bar(), ' ', progressbar.ETA(), '\033[0;0m'], maxval=len(states_verbose.keys())).start()
for state in states_verbose:
    ouput = json.dumps(states_verbose[state])

    if not os.path.exists('no-callback/{}/'.format(state.lower())):
        os.makedirs('no-callback/{}/'.format(state.lower()))
    no_callback = open('no-callback/{}/index.json'.format(state.lower()), 'w')
    no_callback.write(output)
    no_callback.flush()
    no_callback.close()
    if not os.path.exists('with-callback/{}/'.format(state.lower())):
        os.makedirs('with-callback/{}/'.format(state.lower()))
    with_callback = open(
        'with-callback/{}/index.json'.format(state.lower()), 'w')
    with_callback.write('zipapicallback({});'.format(output))
    with_callback.flush()
    with_callback.close()
    bar.update(bar.value + 1)
bar.finish()

bar = progressbar.ProgressBar(widgets=['\033[92m', progressbar.FormatLabel('Outputting County files %(value)8s: '), progressbar.Percentage(
), ' ', progressbar.Bar(), ' ', progressbar.ETA(), '\033[0;0m'], maxval=len(counties_verbose.keys())).start()
for county in counties_verbose:
    county_data = counties_verbose[county]
    state = county_data['region']['abbr'].lower()
    county_name = county_data['name'].decode(
        'utf-8').lower().split(', ')[0].replace(' ', '-')
    ouput = json.dumps(county_data)
    if not os.path.exists('no-callback/{}/{}/'.format(state, county_name)):
        os.makedirs('no-callback/{}/{}/'.format(state, county_name))
    no_callback = open(
        'no-callback/{}/{}/index.json'.format(state, county_name), 'w')
    no_callback.write(output)
    no_callback.flush()
    no_callback.close()
    if not os.path.exists('with-callback/{}/{}/'.format(state, county_name)):
        os.makedirs('with-callback/{}/{}/'.format(state, county_name))
    with_callback = open(
        'with-callback/{}/{}/index.json'.format(state, county_name), 'w')
    with_callback.write('zipapicallback({});'.format(output))
    with_callback.flush()
    with_callback.close()
    bar.update(bar.value + 1)
bar.finish()

bar = progressbar.ProgressBar(widgets=['\033[92m', progressbar.FormatLabel('Outputting City files %(value)10s: '), progressbar.Percentage(
), ' ', progressbar.Bar(), ' ', progressbar.ETA(), '\033[0;0m'], maxval=len(localities.keys())).start()
for locality in localities:
    locality_data = localities[locality]
    state = locality_data['region']['abbr'].lower()
    locality_name = locality_data['name'].decode(
        'utf-8').lower().split(', ')[0].replace(' ', '-')
    ouput = json.dumps(locality_data)
    if not os.path.exists('no-callback/{}/{}/'.format(state, locality_name)):
        os.makedirs('no-callback/{}/{}/'.format(state, locality_name))
    no_callback = open(
        'no-callback/{}/{}/index.json'.format(state, locality_name), 'w')
    no_callback.write(output)
    no_callback.flush()
    no_callback.close()
    if not os.path.exists('with-callback/{}/{}/'.format(state, locality_name)):
        os.makedirs('with-callback/{}/{}/'.format(state, locality_name))
    with_callback = open(
        'with-callback/{}/{}/index.json'.format(state, locality_name), 'w')
    with_callback.write('zipapicallback({});'.format(output))
    with_callback.flush()
    with_callback.close()
    bar.update(bar.value + 1)
bar.finish()
