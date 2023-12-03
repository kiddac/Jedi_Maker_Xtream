#!/bin/bash
# Script to generate po files outside of the normal build process
#  
# Pre-requisite:
# The following tools must be installed on your system and accessible from path
# gawk, find, xgettext, sed (GNU version), python, msguniq, msgmerge, msgattrib, msgfmt, msginit
#
# Run this script from within the locale folder.
#
# Author: Pr2
# Version: 1.0
#
Plugin=JediMakerXtream
FilePath=/LC_MESSAGES/
printf "Po files update/creation from script starting.\n"
languages=($(ls -d ./*/ | sed 's/\/$//g; s/.*\///g'))

#
# Arguments to generate the pot and po files are not retrieved from the Makefile.
# So if parameters are changed in Makefile please report the same changes in this script.
#

printf "Creating temporary file $Plugin-py.pot\n"
find .. -name "*.py" -exec xgettext --no-wrap -L Python --from-code=UTF-8 -kpgettext:1c,2 --add-comments="TRANSLATORS:" -d $Plugin -s -o $Plugin-py.pot {} \+
sed --in-place $Plugin-py.pot --expression=s/CHARSET/UTF-8/
OLDIFS=$IFS
IFS=" "
for lang in "${languages[@]}" ; do
	if [ -f $lang$FilePath$Plugin.po ]; then 
		printf "Updating existing translation file %s.po\n" $lang
		msgmerge --backup=none --no-wrap -s -U $lang$FilePath$Plugin.po $Plugin-py.pot && touch $lang$FilePath$Plugin.po
		msgattrib --no-wrap --no-obsolete $lang$FilePath$Plugin.po -o $lang$FilePath$Plugin.po
		msgfmt -o $lang$FilePath$Plugin.mo $lang$FilePath$Plugin.po
	else
		if [ ! -d $lang$FilePath ]; then
			mkdir $lang$FilePath
		fi
		printf "New file created: %s, please add it to github before commit\n" $lang$FilePath$Plugin.po
		msginit -l $lang$FilePath$Plugin.po -o $lang$FilePath$Plugin.po -i $Plugin-py.pot --no-translator
		msgfmt -o $lang$FilePath$Plugin.mo $lang$FilePath$Plugin.po
	fi
done
IFS=$OLDIFS
printf "Po files update/creation from script finished!\n"
