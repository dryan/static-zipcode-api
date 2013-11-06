#! /usr/bin/env python

# you'll need to download http://zips.dryan.io/zip-county.txt into the datasets directory to run this

import os, json, sys, re, progressbar
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

alpha_only      =   re.compile(r'[^A-Za-z]')

zips            =   {}
regions         =   {}

f               =   open('datasets/state-fips.json', 'r')
state_fips      =   json.load(f)
f.close()

f               =   open('datasets/zip.json', 'r')
primary_data    =   json.load(f)
f.close()

to_process      =   len(primary_data.keys()) + 22827944 # the number of county records
bar             =   progressbar.ProgressBar(widgets = ['\033[92m', progressbar.FormatLabel('Processing ZIP Codes %(value)d: '), progressbar.Percentage(), ' ', progressbar.Bar(), ' ', progressbar.ETA(), '\033[0;0m'], maxval = to_process).start()

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

    obj['localities']   =   list(set(obj['localities']))
    obj['localities'].sort()
    zips[z]     =   obj

    bar.update(bar.currval + 1)

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
    bar.update(bar.currval + 1)
f.close()

bar.finish()

sys.stdout.write('\nWriting out the files...\n')
sys.stdout.flush()

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

# make the reverse mapping by STATE/CITY
for i in zips:
    f           =   open('no-callback/%s.json' % i, 'r')
    zip_data    =   json.load(f)
    f.close()

    if not zip_data.get('region', False):
        continue

    if not zip_data.get('region').get('abbr') in regions:
        regions[zip_data.get('region').get('abbr')] =   {
            'fips':         zip_data.get('region').get('fips', ''),
            'name':         zip_data.get('region').get('name', ''),
            'abbr':         zip_data.get('region').get('abbr', ''),
            'localities':   {},
        }

    for locality in zip_data.get('localities', [zip_data.get('locality')]):
        if not alpha_only.sub('', locality).lower() in regions[zip_data.get('region').get('abbr')]['localities']:
            regions[zip_data.get('region').get('abbr')]['localities'][alpha_only.sub('', locality).lower()] =   {
                'name':         locality,
                'postal_codes': [i],
                'counties':     zips[i]['counties'] if i in zips else [],
                'region':   {
                    'fips':         zip_data.get('region').get('fips', ''),
                    'name':         zip_data.get('region').get('name', ''),
                    'abbr':         zip_data.get('region').get('abbr', ''),
                }
            }
        else:
            regions[zip_data.get('region').get('abbr')]['localities'][alpha_only.sub('', locality).lower()]['postal_codes'].append(i)
            regions[zip_data.get('region').get('abbr')]['localities'][alpha_only.sub('', locality).lower()]['counties'] =   regions[zip_data.get('region').get('abbr')]['localities'][alpha_only.sub('', locality).lower()]['counties'] + (zips[i]['counties'] if i in zips else [])

def count_counties(region):
    count   =   0
    for entity in region.get('localities'):
        count   +=  len(region.get('localities').get(entity).get('counties', []))
    return count

def count_postal_codes(region):
    pcs =   []
    for city in region.get('localities', {}):
        pcs =   pcs + region.get('localities').get(city).get('postal_codes')
    return len(set(pcs))

for region in regions:
    region      =   regions.get(region)
    if not region.get('abbr', False) or region.get('abbr') == '-1':
        continue

    for city in region.get('localities', []):
        city    =   region.get('localities').get(city)
        city['postal_codes']    =   list(set(city['postal_codes']))
        city['counties']        =   [dict(t) for t in set([tuple(d.items()) for d in city['counties']])]

    bar     =   progressbar.ProgressBar(widgets = ['\033[92m', progressbar.FormatLabel('Processing ' + region.get('abbr') + ' %(value)d: '), progressbar.Percentage(), ' ', progressbar.Bar(), ' ', progressbar.ETA(), '\033[0;0m'], maxval = len(region.get('localities', []))).start()

    region_data =   {
        'name':         region.get('name'),
        'abbr':         region.get('abbr'),
        'fips':         region.get('fips'),
        'postal_codes': count_postal_codes(region),
        'localities':   len(region.get('localities')),
        'counties':     count_counties(region),
    }

    if not os.path.exists(os.path.join('no-callback', region.get('abbr').lower())):
        os.mkdir(os.path.join('no-callback', region.get('abbr').lower()))
    f           =   open(os.path.join('no-callback', region.get('abbr').lower(), 'index.json'), 'w')
    f.write(json.dumps(region_data))
    f.flush()
    f.close()

    if not os.path.exists(os.path.join('with-callback', region.get('abbr').lower())):
        os.mkdir(os.path.join('with-callback', region.get('abbr').lower()))
    f           =   open(os.path.join('with-callback', region.get('abbr').lower(), 'index.json'), 'w')
    f.write('zipapicallback(%s);' % json.dumps(region_data))
    f.flush()
    f.close()

    for locality in region['localities']:
        locality    =   region['localities'].get(locality)

        if not os.path.exists(os.path.join('no-callback', region.get('abbr').lower(), alpha_only.sub('', locality.get('name')).lower())):
            os.mkdir(os.path.join('no-callback', region.get('abbr').lower(), alpha_only.sub('', locality.get('name')).lower()))
        f           =   open(os.path.join('no-callback', region.get('abbr').lower(), alpha_only.sub('', locality.get('name')).lower(), 'index.json'), 'w')
        f.write(json.dumps(locality))
        f.flush()
        f.close()

        if not os.path.exists(os.path.join('with-callback', region.get('abbr').lower(), alpha_only.sub('', locality.get('name')).lower())):
            os.mkdir(os.path.join('with-callback', region.get('abbr').lower(), alpha_only.sub('', locality.get('name')).lower()))
        f           =   open(os.path.join('with-callback', region.get('abbr').lower(),alpha_only.sub('', locality.get('name')).lower(), 'index.json'), 'w')
        f.write(json.dumps(locality))
        f.flush()
        f.close()

    bar.finish()

sys.stdout.write('\nFinished\n')
sys.stdout.flush()

sys.exit(os.EX_OK)