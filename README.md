# Static ZIP Code API

Simple "API" for retrieving information about a given ZIP Code via (several thousand) static files. The idea is to host these in a CDN like Amazon S3.

There are two flavors: vanilla JSON and JSONP with a hardcoded callback function of `zipapicallback`.

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

    {
        "zip_code": "37415",
        "lat":      35.116285,
        "lng":      -85.28466,
        "locality": "Red Bank",
        "region":   {
            "abbr": "TN",
            "name": "Tennessee"
        }
    }

Hat tip to [Ziptastic](http://daspecster.github.com/ziptastic/).
