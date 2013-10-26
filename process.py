#! /usr/bin/env python

import os, json, sys
from titlecase import titlecase

us_states       =   {
    'AA': 'Armed Forces Americas',
    'AE': 'Armed Forces Europe',
    'AK': 'Alaska',
    'AL': 'Alabama',
    'AP': 'Armed Forces Pacific',
    'AR': 'Arkansas',
    'AS': 'American Samoa',
    'AZ': 'Arizona',
    'CA': 'California',
    'CO': 'Colorado',
    'CT': 'Connecticut',
    'DC': 'District of Columbia',
    'DE': 'Delaware',
    'FL': 'Florida',
    'GA': 'Georgia',
    'GU': 'Guam',
    'HI': 'Hawaii',
    'IA': 'Iowa',
    'ID': 'Idaho',
    'IL': 'Illinois',
    'IN': 'Indiana',
    'KS': 'Kansas',
    'KY': 'Kentucky',
    'LA': 'Louisiana',
    'MA': 'Massachusetts',
    'MD': 'Maryland',
    'ME': 'Maine',
    'MI': 'Michigan',
    'MN': 'Minnesota',
    'MO': 'Missouri',
    'MP': 'Northern Mariana Islands',
    'MS': 'Mississippi',
    'MT': 'Montana',
    'NC': 'North Carolina',
    'ND': 'North Dakota',
    'NE': 'Nebraska',
    'NH': 'New Hampshire',
    'NJ': 'New Jersey',
    'NM': 'New Mexico',
    'NV': 'Nevada',
    'NY': 'New York',
    'OH': 'Ohio',
    'OK': 'Oklahoma',
    'OR': 'Oregon',
    'PA': 'Pennsylvania',
    'PR': 'Puerto Rico',
    'RI': 'Rhode Island',
    'SC': 'South Carolina',
    'SD': 'South Dakota',
    'TN': 'Tennessee',
    'TX': 'Texas',
    'UT': 'Utah',
    'VA': 'Virginia',
    'VI': 'Virgin Islands',
    'VT': 'Vermont',
    'WA': 'Washington',
    'WI': 'Wisconsin',
    'WV': 'West Virginia',
    'WY': 'Wyoming'
}

zips            =   {}

f               =   open('datasets/state-fips.json', 'r')
state_fips      =   json.load(f)
f.close()

f               =   open('datasets/zip.json', 'r')
primary_data    =   json.load(f)
f.close()

for z in primary_data:
    valid_state =   True
    for row in primary_data[z]:
        if not row['region'] in us_states:
            valid_state =   False
    if not valid_state:
        continue
    obj                 =   {}
    obj['postal_code']  =   z
    obj['type']         =   primary_data[z][0]['type']
    old_file            =   'no-callback/%s.json' % z
    if os.path.exists(old_file):
        f           =   open(old_file, 'r')
        old_data    =   json.load(f)
        f.close()
        if 'lat' in old_data and 'lng' in old_data:
            obj['lat']  =   old_data['lat']
            obj['lng']  =   old_data['lng']
    obj['region']   =   {
        'abbr':     primary_data[z][0]['region'],
        'name':     us_states[primary_data[z][0]['region']],
        'fips':     state_fips[primary_data[z][0]['region']] if primary_data[z][0]['region'] in state_fips else '',
    }
    obj['localities']   =   []
    obj['counties']     =   []
    for row in primary_data[z]:
        if row['primary']:
            obj['locality'] =   row['locality']
        obj['localities'].append(row['locality'])

    obj['localities'].sort()
    zips[z]     =   obj

f               =   open('datasets/zip-county.txt', 'r')
for line in f:
    line    =   line.strip()
    if len(line) >= 29:
        # this is a full record
        zipcode     =   line[0:5]
        state       =   line[23:25]
        fips        =   line[25:28]
        name        =   titlecase(line[28:])

        if(state in us_states and zipcode in zips):
            county  =   {
                'name':     name,
                'fips':     fips,
            }
            if not county in zips[zipcode]['counties']:
                zips[zipcode]['counties'].append(county)
        # else:
        #     print state, zipcode
f.close()

# write the data
for z in zips:
    data    =   json.dumps(zips[z])

    f       =   open('no-callback/%s.json' % z, 'w')
    f.write(data)
    f.flush()
    f.close()

    f       =   open('with-callback/%s.json' % z, 'w')
    f.write('zipapicallback(%s);' % data)
    f.flush()
    f.close()

# fill out placeholder files for non-existent zips
for i in range(0, 100000):
    i       =   '%05d' % i
    if not os.path.exists('no-callback/%s.json' % i):
        f   =   open('no-callback/%s.json' % i, 'w')
        f.write('{}');
        f.flush()
        f.close()
    if not os.path.exists('with-callback/%s.json' % i):
        f   =   open('with-callback/%s.json' % i, 'w')
        f.write('zipapicallback({});')
        f.flush()
        f.close()
