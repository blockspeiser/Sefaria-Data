# encoding=utf-8

import os
from os.path import dirname as loc
from sources.Shulchan_Arukh.ShulchanArukh import *

"""
Marks:

start_ramah        @33
end_ramah          @88

Beur HaGra         !.)
Taz                A[.]  @91
Be'er HaGolah      @44.
Pithei Teshuva     @66(.)

Marks to existing commentaries:
Beit Shmuel        @55.
Chelkat Mechokek   @77(.)
Ba'er Hetev        B.)  @82
"""


if __name__ == "__main__":
    root_dir = loc(loc(loc(os.path.abspath(__file__))))
    xml_loc = os.path.join(root_dir, 'Even_HaEzer.xml')
    if not os.path.exists(xml_loc):
        raise IOError("xml file does not exist. Please run startup.py")

    root = Root(xml_loc)
    base = root.get_base_text()
    filenames = {
        1: os.path.join(root_dir, u'txt_files/Even_Haezer/part_1/אבן העזר חלק א מחבר.txt'),
        2: os.path.join(root_dir, u'txt_files/Even_Haezer/part_2/שולחן ערוך אבן האזל חלק ב מחבר.txt')
    }
    for i in [1,2]:
        filename = filenames[i]
        assert os.path.exists(filename)

        base.remove_volume(i)
        with codecs.open(filename, 'r', 'utf-8') as infile:
            volume = base.add_volume(infile.read(), i)
        assert isinstance(volume, Volume)

        volume.mark_simanim(u'@22([\u05d0-\u05ea]{1,3})', specials={
            u'@00': {'name': u'topic'},
            u'@13': {'name': u'Halitza', 'end': u'!end!'},
            u'@14': {'name': u'Get', 'end': u'!end!'}
        })
        print "Validating Simanim"
        volume.validate_simanim()

        bad = volume.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})', specials={u'@12': {'name': u'title'}})
        print "Validating Seifim"
        for i in bad:
            print i
        volume.validate_seifim()

        errors = volume.format_text('@33', '@88', 'ramah')
        for i in errors:
            print i

        codes = [u'!.) -Gra', u'@91[.] -Taz', u'@66 -Pithei Teshuva', u'@55 -Beit Shmuel', u'@77 -Chelkat Mechokek', u'@82.) -Ba\'er Hetev']
        patterns = [ur'!{}', ur'@91\[{}\]', ur'@66{}', ur'@55{}', ur'@77\({}\)', ur'@82{}\)']
        patterns = [pattern.format(ur'([\u05d0-\u05ea]{1,3})') for pattern in patterns]


        volume.validate_references(ur'@44([\u05d0-\u05ea])', u'@44 -Be\'er HaGolah', key_callback=he_ord)
        for pattern, code in zip(patterns, codes):
            volume.validate_references(pattern, code)

        # correct_marks_in_file(filename, u'@22', ur'@82([\u05d0-\u05ea]{1,3})\)', overwrite=False)
