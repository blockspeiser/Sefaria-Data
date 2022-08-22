import django

django.setup()

import csv
import re
import requests
from bs4 import BeautifulSoup
import PIL
from PIL import Image
from io import BytesIO
from base64 import b64decode, b64encode
import statistics

from sefaria.model import *

# TODO - Line 60 manually fix footnote issue (i.e. manually put in footnotes

def convert_base_64_img(halakha):
    ref_name = halakha['ref'].lower()
    ref_name = re.sub(" ", "", ref_name)
    ref_name = re.sub("\.", "_", ref_name)
    filename = f"{ref_name}_img.jpg"
    text = halakha['text']
    tags = re.findall("<img.*?>", text)
    for tag in tags:
        url = re.findall(r"src=\"(.*?)\"", tag)[0]
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        orig_height = img.size[1]
        orig_width = img.size[0]
        if orig_width > 550:
            percent = 550 / float(orig_width)
            height = int(float(orig_height) * float(percent))
            img = img.resize((550, height), PIL.Image.ANTIALIAS)
        img = img.save(f"images/{filename}")
        file = open("./images/{}".format(filename), 'rb')
        data = file.read()
        file.close()
        data = b64encode(data)
        new_tag = '<img src="data:image/{};base64,{}"></img>'.format('jpg', str(data)[2:-1])
        text = text.replace(tag, new_tag)
    return text


def setup_data():
    """
    This function reads the CSV from the scraping, and sets up a list of Chabad specific Rambam names,
    as well as a list of dictionaries of the scraping data for easy manipulation later
    """
    chabad_book_names = []
    mishneh_torah_list = []
    with open('mishneh_torah_data_scraped_ftns.csv', newline='') as csvfile:
        r = csv.reader(csvfile, delimiter=',')
        next(r, None)
        for row in r:
            book_ref = row[0]

            # TODO - fix this one for footnotes?
            # Texts which are exceptions to the scrape
            if book_ref == "Tefillin, Mezuzah and Sefer Torah 8.4":
                txt = "<p>Since I have seen great confusion about these matters in all the scrolls I have seen, and similarly, the masters of the tradition who have written down and composed [texts] to make it known [which passages] are <i>p'tuchot</i> and which are <i>s'tumot</i> are divided with regard to the scrolls on which to rely, I saw fit to write down the entire list of all the passages in the Torah that are <i>s'tumot</i> and <i>p'tuchot</i>, and also the form of the songs. In this manner, all the scrolls can be corrected and checked against these [principles].<a class=""footnote_ref"" href=""javascript:doFootnote('9a925430');"" name=""footnoteRef9a925430"">9</a></p><p>The scroll on which I relied on for [clarification of] these matters was a scroll renowned in Egypt, which includes all the 24 books [of the Bible]. It was kept in Jerusalem for many years so that scrolls could be checked from it. Everyone relies upon it because it was corrected by ben Asher,<a class=""footnote_ref"" href=""javascript:doFootnote('10a925430');"" name=""footnoteRef10a925430"">10</a> who spent many years writing it precisely, and [afterward] checked it many times.</p><p>I relied [on this scroll] when I wrote a Torah scroll according to law.</p> <p class=\"child_title\">The Book of <span class=\"glossary_item\" glossary_item=\"34157\">Genesis</span></p><p>יהי רקיע יקוו המים יהי מאורות ישרצו המים תוצא הארץ ויכלו אלה תולדות השמים כולן פתוחות והן שבע פרשיות אל האשה אמר ולאדם אמר שתיהן סתומות ויאמר יי' אלהים פתוחה והאדם ידע זה ספר ויחי שת ויחי אנוש ויחי קינן ויחי מהללאל ויחי ירד ויחי חנוך ויחי מתושלח ויחי למך ויחי נח אחת עשרה פרשיות אלו כולן סתומות וירא יי' אלה תולדת נח שתיהן פתוחות ויאמר אלהים לנח וידבר אלהים אל נח ויאמר אלהים אל נח שלשתן סתומות ויהיו בני נח ואלה תולדת בני נח שתיהן פתוחות וכנען ילד ולשם ילד שתיהן סתומות ויהי כל הארץ שפה אחת אלה תולדת שם שתיהן פתוחות וארפכשד חי ושלח חי ויחי עבר ויחי פלג ויחי רעו ויחי שרוג ויחי נחור ויחי תרח כולן סתומות השמונה פרשיות ויאמר יי' אל אברם ויהי רעב ויהי בימי אמרפל שלשתן פתוחות אחר הדברים ושרי אשת אברם ויהי אברם ויאמר אלהים אל אברהם ארבעתן סתומות וירא אליו פתוחה ויסע משם ויי' פקד את שרה שתיהן סתומות ויהי בעת ההוא ויהי אחר ויהי אחרי הדברים ויהיו חיי שרה ארבעתן פתוחות ואברהם זקן סתומה ויסף אברהם ואלה תלדת ישמעאל ואלה תולדת יצחק ויהי רעב ארבעתן פתוחות ויהי עשו ויהי כי זקן יצחק ויצא יעקב שלשתן סתומות וישלח יעקב פתוחה ויבא יעקב ותצא דינה שתיהן סתומות ויאמר אלהים וירא אלהים ויהיו בני יעקב ואלה תלדות עשו ארבעתן פתוחות אלה בני שעיר סתומה ואלה המלכים וישב יעקב ויהי בעת שלשתן פתוחות ויוסף הורד מצרימה סתומה ויהי אחר הדברים ויהי מקץ שתיהן פתוחות: ויגש אליו ואלה שמות ואת יהודה שלשתן סתומות ויהי אחרי הדברים ויקרא יעקב שמעון ולוי יהודה זבולן יששכר כולן פתוחות והן שש דן גד מאשר נפתלי בן פרת יוסף חמשתן סתומות בנימין פתוחה </p><p>There are 43 passages that are <i>p'tuchot</i> and 48 passages that are <i>s'tumot</i>, 91 passages in their entirety.<a class=\"footnote_ref\" href=\"javascript:doFootnote('11a925430');\" name=\"footnoteRef11a925430\">11</a></p>"
            elif book_ref == "Yesodei haTorah 1.1":
                txt = "<p>The foundation of all foundations and the pillar of wisdom is to know that there is a Primary Being who brought into being all existence. All the beings of the heavens, the earth, and what is between them came into existence only from the truth of His being.</p>"
            else:
                txt = row[1]
            mishneh_torah_list.append({'ref': book_ref, 'text': txt})
            book = re.findall(r"(.*) \d*.\d*", book_ref)[0]
            if book not in chabad_book_names:
                chabad_book_names.append(book)
    return chabad_book_names, mishneh_torah_list


def create_book_name_map(chabad_book_names):
    """
    This function creates a map between the Chabad Rambam names to the Sefaria Rambam names
    """
    sefaria_book_names = [
        'Foundations of the Torah',
        'Human Dispositions',
        'Torah Study',
        'Foreign Worship and Customs of the Nations',
        'Repentance',
        'Reading the Shema',
        'Prayer and the Priestly Blessing',
        'Tefillin, Mezuzah and the Torah Scroll',
        'Fringes',
        'Blessings',
        'Circumcision',
        'The Order of Prayer',
        'Sabbath',
        'Eruvin',
        'Rest on the Tenth of Tishrei',
        'Rest on a Holiday',
        'Leavened and Unleavened Bread',
        'Shofar, Sukkah and Lulav',
        'Sheqel Dues',
        'Sanctification of the New Month',
        'Fasts',
        'Scroll of Esther and Hanukkah',
        'Marriage',
        'Divorce',
        'Levirate Marriage and Release',
        'Virgin Maiden',
        'Woman Suspected of Infidelity',
        'Forbidden Intercourse',
        'Forbidden Foods',
        'Ritual Slaughter',
        'Oaths',
        'Vows',
        'Nazariteship',
        'Appraisals and Devoted Property',
        'Diverse Species',
        'Gifts to the Poor',
        'Heave Offerings',
        'Tithes',
        'Second Tithes and Fourth Year\'s Fruit',
        'First Fruits and other Gifts to Priests Outside the Sanctuary',
        'Sabbatical Year and the Jubilee',
        'The Chosen Temple',
        'Vessels of the Sanctuary and Those who Serve Therein',
        'Admission into the Sanctuary',
        'Things Forbidden on the Altar',
        'Sacrificial Procedure',
        'Daily Offerings and Additional Offerings',
        'Sacrifices Rendered Unfit',
        'Service on the Day of Atonement',
        'Trespass',
        'Paschal Offering',
        'Festival Offering',
        'Firstlings',
        'Offerings for Unintentional Transgressions',
        'Offerings for Those with Incomplete Atonement',
        'Substitution',
        'Defilement by a Corpse',
        'Red Heifer',
        'Defilement by Leprosy',
        'Those Who Defile Bed or Seat',
        'Other Sources of Defilement',
        'Defilement of Foods',
        'Vessels',
        'Immersion Pools',
        'Damages to Property',
        'Theft',
        'Robbery and Lost Property',
        'One Who Injures a Person or Property',
        'Murderer and the Preservation of Life',
        'Sales',
        'Ownerless Property and Gifts',
        'Neighbors',
        'Agents and Partners',
        'Slaves',
        'Hiring',
        'Borrowing and Deposit',
        'Creditor and Debtor',
        'Plaintiff and Defendant',
        'Inheritances',
        'The Sanhedrin and the Penalties within their Jurisdiction',
        'Testimony',
        'Rebels',
        'Mourning',
        'Kings and Wars'
    ]

    # Confirmed that book names aligned, creating map
    name_map = {}
    for i in range(len(chabad_book_names)):
        name_map[chabad_book_names[i]] = sefaria_book_names[i]
    return name_map


def rename_refs_to_sefaria(mishneh_torah_list, name_map):
    """
    This function massages the Chabad Refs into Sefaria refs for the data list/dictionary
    """
    new_mt_list = []
    for halakha in mishneh_torah_list:
        ref = halakha['ref']
        book = re.findall(r"(.*) \d*.\d*", ref)[0]
        sef_book = name_map[book]
        sefaria_ref = re.sub(r"[^0-9.]+", f"{sef_book} ", ref)
        new_mt_list.append({'ref': sefaria_ref, 'text': halakha['text']})

    return new_mt_list


def flag_no_punc(mt_list):
    count = 0
    new_list = []
    for halakha in mt_list:
        # clean extra whitespace
        text = halakha['text'].strip()
        if text[-1] not in [".", "?", "!", ";", "\'", "\"", ">", "”"]:
            count += 1
            new_list.append({'ref': halakha['ref'],
                             'text': text,
                             'flag': True})
        else:
            new_list.append({'ref': halakha['ref'],
                             'text': text,
                             'flag': False})
    print(f"{count} flagged of {len(new_list)}")
    return new_list


def export_cleaned_data_to_csv(mt_list):
    """
    This function writes the cleaned data to a new CSV
    """
    with open('mishneh_torah_data_cleaned.csv', 'w+') as csvfile:
        headers = ['ref', 'text', 'flag', 'msg']
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writerows(mt_list)


def strip_p_for_br(mt_list):
    new_list = []
    for halakha in mt_list:
        txt = halakha['text']
        br_txt = re.sub(r"</p>\n<p>", "<br>", txt)
        clean_txt = re.sub(r"<p>|</p>", "", br_txt)  # remove remaining <p>
        new_list.append({'ref': halakha['ref'], 'text': clean_txt})
    return new_list


def img_convert(mt_list):
    new_mt_list = []
    for halakha in mt_list:
        cur_dict = {}
        if 'img' in halakha['text']:
            img_txt = convert_base_64_img(halakha)
            cur_dict['ref'] = halakha['ref']
            cur_dict['text'] = img_txt
        else:
            cur_dict['ref'] = halakha['ref']
            cur_dict['text'] = halakha['text']
        new_mt_list.append(cur_dict)
    return new_mt_list


# Hebrew length validation
def generate_stats(mt_list):
    ratio_list = []
    ratio_aggregate = 0

    for halakha in mt_list:
        en_text = halakha['text']
        hebrew_text = Ref(f"Mishneh Torah, {halakha['ref']}").text('he').text

        ratio_he_to_en = len(hebrew_text) / len(en_text)
        ratio_aggregate += ratio_he_to_en
        ratio_list.append(ratio_he_to_en)

    mean_of_ratios = ratio_aggregate / (len(mt_list))
    stdev = statistics.stdev(ratio_list)
    return mean_of_ratios, stdev


def stats_flag(mt_list):
    new_list = []
    mean, stdev = generate_stats(mt_list)
    for halakha in mt_list:
        en_text = halakha['text']
        hebrew_text = Ref(f"Mishneh Torah, {halakha['ref']}").text('he').text

        cur_ratio = len(hebrew_text) / len(en_text)
        two_sd_above = mean + (2 * stdev)
        two_sd_below = mean - (2 * stdev)

        if cur_ratio > two_sd_above or cur_ratio < two_sd_below:
            flag = True
            msg = "Not within 2 stdev"
        else:
            flag = False
            msg = ""

        new_list.append({'ref': halakha['ref'], 'text': halakha['text'], 'flag': flag, 'msg': msg})
    return new_list


def html_clean_up(mt_list):
    new_list = []
    for halakha in mt_list:
        txt = halakha['text']

        # Remove number of quotes from footnote
        if "footnote" in txt:
            txt = re.sub("\"\"", "\"", txt)

        # Massage links to text references into Sefaria form
        links = re.findall(r"<a href=.*?>(.*?)<\/a>", txt)
        for link in links:

            # Add escape characters to links data for matching
            if ")" in link or "(" in link:
                re_link = re.sub(r"\)", "\\)", link)
                re_link = re.sub(r"\(", "\\(", re_link)
            else:
                re_link = link
            clean_link = re.sub(r"[^A-Za-z :0-9]", " ", link)
            patt = f"<a href=.*?>{re_link}<\/a>"
            txt = re.sub(patt, clean_link, txt)

        # Add the appropriate superscript class
        sups = re.findall(r"<sup>(.*?)</sup><i class=\"footnote\">", txt)
        for sup in sups:
            patt = f"<sup>{sup}</sup><i class=\"footnote\">"
            replacement = f"<sup class=\"footnote-marker\">{sup}</sup><i class=\"footnote\">"
            txt = re.sub(patt, replacement, txt)

        new_list.append({'ref': halakha['ref'], 'text': txt})
    return new_list


if __name__ == '__main__':
    chabad_book_names, mishneh_torah_list = setup_data()
    name_map = create_book_name_map(chabad_book_names)
    mishneh_torah_list = rename_refs_to_sefaria(mishneh_torah_list, name_map)
    mishneh_torah_list = strip_p_for_br(mishneh_torah_list)
    mishneh_torah_list = flag_no_punc(mishneh_torah_list)
    mishneh_torah_list = img_convert(mishneh_torah_list)
    # mishneh_torah_list = stats_flag(mishneh_torah_list)
    mishneh_torah_list = html_clean_up(mishneh_torah_list)
    export_cleaned_data_to_csv(mishneh_torah_list)