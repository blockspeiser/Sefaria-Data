# -*- coding: utf-8 -*-
import os
import re
import sys
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from sources.functions import *
import re
import codecs
from fuzzywuzzy import fuzz

"""
Zraaim, Moed, Nashim:
Lines with "$" are skipped
@01 הקדמה 
@00פרק 
@11 משנה
@22 תחילת קטע
@33 תחילת טקסט רגיל 
@44 תחילת קטע (לא דיבור המתחיל) (ERASE)
@55 המשך מקטע חדש ללא דיבור המתחיל (ERASE)
#*) הערה תחתחית
@77 תחילת הערה
@88 סוף הערה (ALSO @78)
@99 כותר סיום
ALSO ERASE: "#", "T", and replace *) with *

Nezikin, Kadshim, Taharos:
@00 Perek
@22 Mishna
@01 Intro
@11 Start DH
@33 End DH
"""
markers_1 = {"Intro":u"@01", "Outro":u"@99", "Perek":u"@00", "Mishna":u"@11", "DH Start": u"@22", "DH End": u"@33", "ERASE":[u"@99",u"@01",u"@44",u"@55",u"#",u"T"]}
markers_2 = {"Intro":u"@01", "Outro": "NONE","Perek":u"@00", "Mishna":u"@22", "DH Start": u"@11", "DH End": u"@33", "ERASE":[u"@01"]}

#first, create index of english and hebrew titles. Since our titles are in hebrew, this is set as the key
tractate_titles = {}
for tractate_title in library.get_indexes_in_category("Mishnah"):
    he_title = library.get_index(tractate_title).get_title("he")
    tractate_titles[he_title]=tractate_title
sedarim = [u"זרעים",u"מועד",u"נשים",u"נזיקין",u"קדשים",u"טהרות"]
#some sedarim have different markings
sedarim_group_1 = [u"זרעים",u"מועד",u"נשים"]
class Tractate:
    pass
def ms_post_term():
    #for posting commentary term for first time
    term_obj = {
        "name": "Melechet Shlomo",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "Melechet Shlomo",
                "primary": True
            },
            {
                "lang": "he",
                "text": u'מלאכת שלמה',
                "primary": True
            }
        ]
    }
    post_term(term_obj)
            
def ms_post_index(tractate_object):   
    record = JaggedArrayNode()
    record.add_title('Melechet Shlomo on '+tractate_object.record_name_en, 'en', primary=True)
    record.add_title(u'מלאכת שלמה על'+' '+tractate_object.record_name_he, 'he', primary=True)
    record.key = 'Melechet Shlomo on '+tractate_object.record_name_en
    record.depth = 3
    record.addressTypes = ["Integer", "Integer", "Integer"]
    record.sectionNames = ["Perek", "Mishnah", "Comment"]
    record.validate()

    index = {
        "title":'Melechet Shlomo on '+tractate_object.record_name_en,
        "base_text_titles": [
          tractate_object.record_name_en
        ],
        "dependence": "Commentary",
        "categories":["Mishnah","Commentary","Melechet Shlomo"],
        "schema": record.serialize()
    }
    post_index(index,weak_network=True)
def ms_post_text(tractate_object):
    with open(tractate_object.file_extension) as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    print tractate_object.record_name_en
    tractate_array = make_perek_array(tractate_array.record_name_en)
    current_perek=1
    current_mishna=1
    in_next_mishna=[]
    for line in lines:
        if tractate_object.markers["Perek"] in line:
            current_perek = getGematria(line.replace(u"פרק",""))
            current_mishna = 1
        elif tractate_object.markers["Mishna"] in line:
            current_mishna = getGematria(line)
            while len(in_next_mishna)>0:
                tractate_array[current_perek-1][current_mishna-1].append(edit_lines(in_next_mishna.pop(0)))
        elif tractate_object.markers["Intro"] in line:
            in_next_mishna.append(line)
        else:
            tractate_array[current_perek-1][current_mishna-1].append(edit_lines(line))
def edit_lines(tractate_object,line):
    for uni in tractate_object.markers["ERASE"]:
        line = line.replace(uni, u"")
    line = line.replace(tractate_object.markers["DH Start"],u"<b>").replace(tractate_object.markers["DH End"],u"</b>")
    return line
def make_perek_array(book):
    tc = TextChunk(Ref(book), "he")
    return_array = []
    for x in range(len(tc.text)):
        return_array.append([])
    for index, perek in enumerate(return_array):
        tc = TextChunk(Ref(book+" "+str(index+1)), "he")
        for x in range(len(tc.text)):
            return_array[index].append([])
    return return_array
    
def get_record_name(title):
    return highest_fuzz(tractate_titles.keys(), title)
posting_term = False
posting_index = False
posting_text= True
admin_links = []
page_links = []
folder_names=[x[0]for x in os.walk("files")][1:]
def get_seder(folder_title):
    return highest_fuzz(sedarim, folder_title)
#bad experiences with fuzzy wuzzy's .process and unicode...
def highest_fuzz(input_list, input_item):
    highest_ratio = 0
    best_match = u''
    for item in input_list:
        if fuzz.ratio(input_item,item)>highest_ratio:
            best_match=item
            highest_ratio=fuzz.ratio(input_item,item)
    return best_match
if posting_term:
    ms_post_term()
if posting_text:
    f = open("MS Intro Table.csv","w")
    f.write("Tractate, Component, Status")
    f.close()
    f = open("MS Intro Content.txt","w")
    f.write('')
    f.close()
for folder in folder_names:
    for ms_file in os.listdir(folder):
        if ".txt" in ms_file:
            current_tractate = Tractate()
            current_tractate.file_extension = folder+"/"+ms_file
            current_tractate.seder = get_seder(folder.decode('utf8','replace'))
            current_tractate.markers = markers_1 if current_tractate.seder in sedarim_group_1 else markers_2
            #a handful of ms_files don't have the word מסכת in them
            if "מסכת" in ms_file:
                current_tractate.tractate_name_he = re.search(r"(?<=מסכת).*(?=.txt)",ms_file).group().strip().decode('utf8','replace')
            else:
                current_tractate.tractate_name_he = re.search(r"(?<=שלמה).*(?=.txt)",ms_file).group().strip().decode('utf8','replace')
            current_tractate.record_name_he = get_record_name(current_tractate.tractate_name_he)
            current_tractate.record_name_en = tractate_titles[current_tractate.record_name_he]
            admin_links.append("localhost:8000/admin/reset/Melechet Shlomo on "+current_tractate.record_name_en)
            page_links.append("http://proto.sefaria.org/Melechet Shlomo_on_"+current_tractate.record_name_en)
            if posting_index:
                ms_post_index(current_tractate)
            if posting_text:
                ms_post_text(current_tractate)
    """for writing record
    
    the commentary is highly irregular, with each tractate having any number of the following:
     (1) intro
     (2) outro
     (3) random out of index portion
    this method returns an array of which, if any, of these is in a given tractate. For (3), the location of the comment
        is given as well.
    
    def get_index_details(tractate_object):
        with open(tractate_object.file_extension) as myfile:
            lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
        current_perek = 0
        current_mishna = 0
        details = {"Other":[]}
        for line in lines:
            if tractate_object.markers["Perek"] in line:
                current_perek = getGematria(line.replace(u"פרק",""))
                current_mishna = 0
            elif tractate_object.markers["Mishna"] in line:
                current_mishna = getGematria(line)
            elif tractate_object.markers["Intro"] in line:
                if current_mishna ==0:
                    details["Intro"]=line
                else:
                    details["Other"].append([[current_perek,current_mishna],line])
            elif tractate_object.markers["Outro"] in line:
              details["Outro"]=line
        return details  
    
    f = open("MS Intro Table.csv","a")
    details = get_index_details(tractate_object)
    if "Intro" in details:
        f.write(tractate_object.record_name_en+", Intro\n")
    if "Other" in details:
        for index in details["Other"]:
            f.write(tractate_object.record_name_en+", "+str(index[0][0])+":"+str(index[0][1])+"\n")
    if "Outro" in details:
        f.write(tractate_object.record_name_en+", Outro\n")
    f.close()
    f = open("MS Intro Content.txt","a")
    if "Intro" in details:
        f.write(tractate_object.record_name_en+", Intro\n")
        f.write(details["Intro"].encode('utf8'))
        f.write("\n______________________________________\n")
    if "Other" in details:
        for index in details["Other"]:
            f.write(tractate_object.record_name_en+", "+str(index[0][0])+":"+str(index[0][1])+"\n")
            f.write(index[1].encode('utf8'))
            f.write("\n______________________________________\n")
    if "Outro" in details:
        f.write(tractate_object.record_name_en+", Outro\n")
        f.write(details["Outro"].encode('utf8'))
        f.write("\n______________________________________\n")
    f.close()
    """
    """
    for key in details.keys():
        f.write(tractate_object.record_name_en)
        if details[key]!=[]:
            print key, details[key]
            f.write(", "+)
    print ""
    """
    #for line in lines:
        #print line