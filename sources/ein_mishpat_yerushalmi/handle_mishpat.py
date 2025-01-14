
import django

django.setup()
from tqdm import tqdm
superuser_id = 171118
import csv
import re
import os
from sefaria.model import *
from sefaria.utils.talmud import daf_to_section, section_to_daf
from typing import List
from pprint import pprint
import copy
from bs4 import BeautifulSoup
from linking_utilities.dibur_hamatchil_matcher import match_text, match_ref


def html_to_text(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    return soup.get_text()

def simple_tokenizer(text):
    """
    A simple tokenizer that splits text into tokens by whitespace,
    and removes apostrophes and periods from the tokens.
    """

    def remove_nikkud(hebrew_string):
        # Define a regular expression pattern for Hebrew vowel points
        nikkud_pattern = re.compile('[\u0591-\u05BD\u05BF-\u05C2\u05C4\u05C5\u05C7]')

        # Use the sub method to replace vowel points with an empty string
        cleaned_string = re.sub(nikkud_pattern, '', hebrew_string)

        return cleaned_string
    # Replace apostrophes and periods with empty strings
    text = text.replace("'", "")
    text = text.replace(".", "")
    text = text.replace("׳", "")
    text = text.replace("–", "")
    text = text.replace(";", "")
    text = remove_nikkud(text)

    # Split the text into tokens by whitespace
    tokens = text.split()
    return tokens

def remove_divs_starting_with_text(html_content, prefix):
    soup = BeautifulSoup(html_content, 'html.parser')
    divs_to_remove = [div for div in soup.find_all('div') if div.get_text().strip().startswith(prefix)]
    for div in divs_to_remove:
        div.decompose()

    modified_html = str(soup)
    return modified_html

def get_divs_starting_with_text(html_content, prefix):
    soup = BeautifulSoup(html_content, 'html.parser')
    divs_to_get = [div.get_text().strip() for div in soup.find_all('div') if div.get_text().strip().startswith(prefix)]
    return divs_to_get


def remove_paragraphs_starting_with_text(html_content, prefix):
    soup = BeautifulSoup(html_content, 'html.parser')
    paragraphs_to_remove = [p for p in soup.find_all('p') if p.get_text().strip().startswith(prefix)]
    for p in paragraphs_to_remove:
        p.decompose()

    modified_html = str(soup)

    return modified_html
def remove_elements_by_tag(html_content, tag_names: List):
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag_name in tag_names:
        for element in soup.find_all(tag_name):
            element.decompose()
    return str(soup)


def get_dh(text):
    result = re.sub(r'\$.+?\$', '', text)
    return result
def list_of_tuples_to_csv(data, filename='output.csv'):
    """
    Converts a list of tuples to a CSV file.

    Parameters:
    data (list of tuples): The data to write to the CSV file.
    filename (str): The name of the output CSV file.

    Returns:
    None
    """
    try:
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(data)
        print(f"Data has been written to {filename}")
    except Exception as e:
        print(f"An error occurred: {e}")
def link_markers_to_sefaria_segments(comments_list, masechet_name, chapter_num):
    segments = Ref(f'Jerusalem Talmud {masechet_name} chapter {chapter_num}').all_segment_refs()
    base_text_list = [seg.text('he') for seg in segments]
    links = match_ref(base_text_list, comments_list, simple_tokenizer, dh_extract_method=get_dh, chunks_list=True)
    table = []
    for marker, matched in zip(comments_list, links['matches']):
        tref = matched.tref if matched else ""
        url = "https://www.sefaria.org/"+matched.url() if matched else ""

        table.append( (marker, tref, url) )
    list_of_tuples_to_csv(table)
    print(links)


def extract_with_context(text, span, num_words_before, num_words_after):
    import re

    # Define a regex pattern that includes words and words surrounded by dollar signs
    pattern = r'\$?\b\w+\b\$?'

    # Extracting the span text
    span_text = text[span[0]:span[1]]

    # Finding the start index of the span in terms of word positions
    words = re.findall(pattern, text)
    start_idx = len(re.findall(pattern, text[:span[0]]))

    # Getting the indices of the context words
    start_context = max(0, start_idx - num_words_before)
    end_context = min(len(words), start_idx + num_words_after + len(re.findall(pattern, span_text)))

    # Extracting the relevant words
    context_words = words[start_context:end_context]

    # Join the context words to form the result
    result = ' '.join(context_words)

    return result


def concatenate_lines(input_string):
    lines = input_string.splitlines()
    result = []

    for line in lines:
        stripped_line = line.strip()
        if stripped_line and stripped_line[0].isdigit():
            result.append(line)
        else:
            if result:
                result[-1] += ' ' + line.strip()
            else:
                result.append(line)

    return result
def infer_footnotes_links(html_content):
    divs_text = get_divs_starting_with_text(html_content, 'עין משפט ונר מצוה')
    markers_footnotes = []
    linker = library.get_linker("he")
    for div_text in divs_text:
        lines = concatenate_lines(div_text)
        lines_starting_with_number = [
            line for line in lines if line.lstrip() and line.lstrip().split() and line.lstrip().split()[0][0].isdigit()
        ]
        for line in lines_starting_with_number:
            match = re.search(r'[\u0590-\u05FF]+_[\u0590-\u05FF]+\b', line)
            marker = match.group() if match else None
            if marker:
                doc = linker.link(line, type_filter="citation", with_failures=True)
                for citation in doc.resolved_refs:
                    print(citation.ref)
                    markers_footnotes.append( (marker, citation.pretty_text, citation.ref) )
    list_of_tuples_to_csv(markers_footnotes, 'footnotes_links.csv')
def infer_sefaria_segment_for_markers(html_content, masechet_name, chapter_num):
    pattern = r'\b[\u0590-\u05FF]+_[\u0590-\u05FF]+\b'
    html_content = re.sub(pattern, lambda m: f"${m.group()}$", html_content)
    html_content = remove_divs_starting_with_text(html_content, 'עין משפט ונר מצוה')
    html_content = remove_paragraphs_starting_with_text(html_content, "קישורים")
    html_content = remove_elements_by_tag(html_content, ['h3', 'figure'])
    plain_text = html_to_text(html_content)
    #remove
    #מפרשים:
    #   ^[דף ג עמוד ב]
    #from page
    plain_text = re.sub(r"מפרשים:\s*\^\[.*?\]", '', plain_text)
    # Using re.findall to find all matches
    matches = re.compile(r'\$.+?\$').finditer(plain_text)
    comments = []
    for match in matches:
        match_text = plain_text[match.regs[0][0]:match.regs[0][1]]
        if all(term not in match_text for term in ['מסכת', 'פרק', 'ירושלמי']):
            extraction = extract_with_context(plain_text, (match.regs[0][0], match.regs[0][1]), 0, 5)
            comments.append(extraction)

    for index, c in enumerate(comments):
        print(str(index) + ": " + c)
    link_markers_to_sefaria_segments(comments, masechet_name, chapter_num)

def get_html_files(directory):
    html_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                html_files.append(os.path.join(root, file))

    html_files.sort(key=os.path.getctime)
    for file in html_files:
        yield file


masechtot_dict = {
    # Zeraim (Seeds)
    "ברכות": "Berakhot",
    "פאה": "Peah",
    "דמאי": "Demai",
    "כלאים": "Kilayim",
    "שביעית": "Shevi'it",
    "תרומות": "Terumot",
    "מעשרות": "Ma'asrot",
    "מעשר שני": "Ma'aser Sheni",
    "חלה": "Challah",
    "ערלה": "Orlah",
    "ביכורים": "Bikkurim",

    # Moed (Festivals)
    "שבת": "Shabbat",
    "עירובין": "Eruvin",
    "פסחים": "Pesachim",
    "שקלים": "Shekalim",
    "יומא": "Yoma",
    "סוכה": "Sukkah",
    "ביצה": "Beitzah",
    "ראש השנה": "Rosh Hashanah",
    "תענית": "Taanit",
    "מגילה": "Megillah",
    "מועד קטן": "Moed Katan",
    "חגיגה": "Chagigah",

    # Nashim (Women)
    "יבמות": "Yevamot",
    "כתובות": "Ketubot",
    "נדרים": "Nedarim",
    "נזיר": "Nazir",
    "סוטה": "Sotah",
    "גיטין": "Gittin",
    "קידושין": "Kiddushin",

    # Nezikin (Damages)
    "בבא קמא": "Bava Kamma",
    "בבא מציעא": "Bava Metzia",
    "בבא בתרא": "Bava Batra",
    "סנהדרין": "Sanhedrin",
    "מכות": "Makkot",
    "שבועות": "Shevuot",
    "עבודה זרה": "Avodah Zarah",
    "הוריות": "Horayot",

    # Kodashim (Holy Things)
    "זבחים": "Zevachim",
    "מנחות": "Menachot",
    "חולין": "Chullin",
    "בכורות": "Bekhorot",
    "ערכין": "Arakhin",
    "תמורה": "Temurah",
    "כריתות": "Keritot",
    "מעילה": "Me'ilah",
    "תמיד": "Tamid",
    "מידות": "Middot",
    "קינים": "Kinnim",

    # Taharot (Purities)
    "כלים": "Kelim",
    "אהלות": "Oholot",
    "נגעים": "Nega'im",
    "פרה": "Parah",
    "טהרות": "Taharot",
    "מקואות": "Mikvaot",
    "נידה": "Niddah",
    "מכשירין": "Makhshirin",
    "זבים": "Zavim",
    "טבול יום": "Tovul Yom",
    "ידים": "Yadayim",
    "עוקצים": "Okatzim"
}
if __name__ == '__main__':
    # Reading HTML content from a file
    for wikifile in get_html_files('wiki_data'):
        print(wikifile)
        with open(wikifile, 'r', encoding='utf-8') as file:
            html_content = file.read()

        infer_sefaria_segment_for_markers(html_content, "Shabbat", "1")
    # infer_footnotes_links(html_content)

    # mt = IndexSet({"categories": "Mishneh Torah"}).array()
    # for index in mt:
    #     if index.title.startswith("Mishneh Torah,"):
    #         print(index.all_titles("he")[0])

