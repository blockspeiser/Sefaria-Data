import csv
import urllib, urllib2
from urllib2 import URLError, HTTPError
import json

apikey =  'T3n0rVYhcJXYjNHfnwknGJtnHIOgirP46Rchzh3Ue5k' #Add your API key
#server = 'www.sefaria.org'
server = 'localhost:8000'
#server = 'eph.sefaria.org'

def postLink(link_obj, serializeText = True):
    url = 'http://' + server + '/api/links/'
    if serializeText:
        textJSON = json.dumps(link_obj)
    else:
        textJSON = link_obj
    values = {
        'json': textJSON,
        'apikey': apikey
    }
    data = urllib.urlencode(values)
    print url, data
    req = urllib2.Request(url, data)

    try:
        response = urllib2.urlopen(req)
        print response.read()
    except HTTPError, e:
        print e


if __name__ == '__main__':
    with open('mishnah_mappings.csv', 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        links=[]
        mishnayot = []
        for row in spamreader:
            if len(row[2])<3:
                mishna_start = int(row[2])
                mishna_end = int(row[3])
                mishnayot_count = mishna_end - mishna_start
                a = mishna_start
                while a <= mishna_end:
                    gemara = row[0] + " " + row[4] + ":" + row[5] + "-" + row[6] +":" +  row[7]
                    mishna = "Mishnah " + row[0] +" " +  row[1] + ":" + str(a)
                    link_obj = {
                                "refs": [
                                    gemara,
                                    mishna ],
                                "type": "Mishnah in Talmud",
                                "auto": True,
                                "generated_by": "connect_mishnah",
                                }
                    print row[0] , row[1] , a
                    mishnayot.append(mishna)
                    links.append(link_obj)
                    a += 1


    print len(mishnayot)
    print links[0]
    #links = links[1:len(links)-1]
    #postLink(links)



