# Static ZIP Code API

Simple "API" for retrieving information about a given ZIP Code via (several hundred thousand) static files. The idea is to host these on a static storage service like Amazon S3.

There are two flavors: vanilla JSON and JSONP with a hardcoded callback function of `zipapicallback`.

## Hosted Version

For low traffic usage (less than 1,000 requests per month), you can use http://zips.dryan.io/XXXXX.json. This site uses CORS headers meaning all modern browsers should allow a cross-domain request. If you need to support older browsers, use http://zips.dryan.io/callback/XXXXX.json which uses a hard-coded callback function name of `zipapicallback` (see example below).

For SSL the URIs are https://s3.amazonaws.com/zips.dryan.io/XXXXX.json and https://s3.amazonaws.com/zips.dryan.io/callback/XXXXX.json.

## d3ploy Support

For easy upload to S3, rename `sample-deploy.json` to `deploy.json` and change the "bucket" variable to the name of your target bucket. Then run [d3ploy](http://d3ploy.com/) with the `--all` flag.

## Usage

    function zipapicallback(data) {
        // do something with your data
    }
    $.ajax({
        url:             'http://youramazonbucket.com/37415.json?callback=?',
        cache:           true,
        dataType:        'jsonp',
        jsonpCallback:   'zipapicallback'
    });

## Returned Data

```json
{
    "postal_code": "37415",
    "lat": 35.116285,
    "lng": -85.28466,
    "locality": "Chattanooga",
    "localities": [
        "Chattanooga",
        "Red Bank"
    ],
    "region": {
        "abbr": "TN",
        "name": "Tennessee",
        "fips": "47"
    },
    "counties": [
        {
            "name": "Hamilton",
            "fips": "065"
        }
    ],
    "type": "STANDARD"
}
```

* `lat` and `lng` are the estimated coordinates of the ZIP code's center.
* `locality` is the primary city for the ZIP code as determined by the USPS.
* `localities` is an array of all possible city names as determined by the USPS. Will always at least contain the primary city name.
* `region.fips` is the FIPS (Federal Information Processing Standard) code for this state.
* `counties` is an array of all counties this ZIP code covers according to the USPS.
* Each county has a `fips` property that when combined with `region.fips` gives the full FIPS code for the county. ("47065" in the example above.)
* `type` is one of:
    * STANDARD: a normal ZIP code
    * POBOX: only applies to Post Office Boxes, not street addresses
    * MILITARY: used to route mail for the US military
    * UNIQUE: only applies to a single entity such as 20505 for the CIA in Washington, DC

You can also get data for each US state and some territories, as well as US counties and cities. The URL structures are:

* States: /<state two-letter abbreviation lowercased>/ (Example: /tn/)
* Counties: /<state two-letter abbreviation lowercased>/<county name lowercased, spaces replaced with hyphens>/ (Example: /tn/hamilton/)
* Cities: /<state two-letter abbreviation lowercased>/<city name lowercased, spaces replaced with hyphens>/ (Example: /tn/chattanooga/)


Hat tip to [Ziptastic](http://daspecster.github.com/ziptastic/).

Data compiled from US Census Bureau, US Department of Housing and Urban Development and http://federalgovernmentzipcodes.us.

## Changes in version 2

* `zipcode` is now `postal_code`
* `locality` is now the USPS primary city
* added `localities`, `counties` and `region.fips`
* generated files for all non ZIP codes between 00000-99999 that return an empty object (prevents issues with detecting 404 errors via JSONP)


## Changes in version 3

* updated data sources
* changed process.py to compile.py
* now outputs state, county and city files
