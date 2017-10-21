#! /bin/bash


# This script is a modification of the mmax-xml-import.sh from https://github.com/chardmeier/discomt/tree/master/mmax-import

if [ $# -ne 2 ]
then
	echo "$0 xml directory" 1>&2
	exit 1
fi

xmlcorpus=$1
dir=$2

mmax_skeleton=mmax-import/mmax-skeleton
#xml=xml
xml=xmlstarlet
#tokeniser="/usit/abel/u1/chm/WMT2013.en-fr/tokeniser/tokenizer.perl -l en"
tokeniser=cat

if [ -e $dir ]
then
	echo "$dir already exists." 1>&2
	exit 1
fi

cp -r "$mmax_skeleton" "$dir"

# This is needed because XML Starlet sometimes adds spurious newlines at the
# end of its output.
remove_last_if_empty='
	FNR > 1 {
		print lastline;
	}
	{
		lastline = $0;
	}
	END {
		if(lastline != "")
			print lastline;
	}'

docids=(`$xml sel -t -m "//doc" -v "@docid" -n $xmlcorpus | gawk "$remove_last_if_empty"`)


transform2='
        BEGIN {
                widx = 1;

                print "<?xml version=\"1.0\" encoding=\"UTF-8\" ?>" >COHESION;
                print "<!DOCTYPE markables SYSTEM \"markables.dtd\">" >COHESION;
           	print "<markables xmlns=\"www.eml.org/NameSpaces/sentence\">" >COHESION;
       }

       {
          for(i = 1; i <= NF; i++) {
               x=split($i, values, ":");
               if (length(values[1]) > 0) {
                    n=split(values[1], relations, ",");                                              
                    for (rel in relations) {
                        print "<markable mmax_level=\"ch\" id=\"markable_" MARK++ "\" span=\"word_" widx "\" relid=\"" relations[rel] "\" tran=\"" "0" "\" chid=\"" values[2] "\" />" >COHESION;  
                    }
               }
               if (length(values[3]) > 0) {
                    n=split(values[3], relations, ",");                                              
                    for (rel in relations) {
                        print "<markable mmax_level=\"ch\" id=\"markable_" MARK++ "\" span=\"word_" widx "\" relid=\"" relations[rel] "\" tran=\"" "1" "\" chid=\"" values[2] "\" />" >COHESION;  
                    }

               }
               widx++
          }
        }

        END {
            print MARK
            print "</markables>" >COHESION;

        }
       
       function escape(s) {
                gsub(/&/, "\\&amp;", s);
                gsub(/</, "\\&lt;", s);
                gsub(/>/, "\\&gt;", s);
                return s;
        }' 

      

transform='
	BEGIN {
		widx = 1;
		sidx = 0;

		print "<?xml version=\"1.0\" encoding=\"UTF-8\" ?>" >WORDS;
		print "<!DOCTYPE words SYSTEM \"words.dtd\">" >WORDS;
		print "<words>" >WORDS; 

		print "<?xml version=\"1.0\" encoding=\"UTF-8\" ?>" >SENTENCES;
		print "<!DOCTYPE markables SYSTEM \"markables.dtd\">" >SENTENCES;
		print "<markables xmlns=\"www.eml.org/NameSpaces/sentence\">" >SENTENCES;
	}

	{
		firstword = widx;
		for(i = 1; i <= NF; i++)
			print "<word id=\"word_" widx++ "\">" escape($i) "</word>" >WORDS;
		lastword = widx - 1;

		print "<markable mmax_level=\"sentence\" orderid=\"" sidx "\" id=\"markable_" MARK++ "\" span=\"word_" firstword "..word_" lastword "\" />" >SENTENCES;
                sidx++
	}

	END {
                print MARK
		print "</words>" >WORDS;
		print "</markables>" >SENTENCES;
	}

	function escape(s) {
		gsub(/&/, "\\&amp;", s);
		gsub(/</, "\\&lt;", s);
		gsub(/>/, "\\&gt;", s);
		return s;
	}'

for ((i=0; i<${#docids[@]}; i++))
do
	id=${docids[$i]}
	name="`printf '%03d' $i`_`echo $id | sed 's/[/\\]/_/g'`"
	echo "$id => $name" 1>&2

	mark=$($xml sel -t -m "//doc[@docid='$id']//seg" -v 'normalize-space(.)' -n $xmlcorpus |
		gawk "$remove_last_if_empty" |
		$xml unesc |
		$tokeniser 2>/dev/null |
		gawk -v MARK="$mark" -v WORDS=$dir/Basedata/${name}_words.xml -v SENTENCES=$dir/markables/${name}_sentence_level.xml "$transform")
	echo $mark
        mark=$($xml sel -t -m "//doc[@docid='$id']//seg/w" -v "@rel" -o ":" -v "@ch" -o ":" -v "@tran" -n $xmlcorpus |
                 gawk "$remove_last_if_empty" |
                 $xml unesc |
                 $tokeniser 2>/dev/null |
                 gawk -v MARK="$mark" -v COHESION=$dir/markables/${name}_ch_level.xml "$transform2")

	cat <<EOF >$dir/$name.mmax
<?xml version="1.0" encoding="UTF-8"?>
<mmax_project>
<words>${name}_words.xml</words>
<keyactions></keyactions>
<gestures></gestures>
</mmax_project>
EOF
done
