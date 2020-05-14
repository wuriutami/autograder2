#!/bin/bash

strings=( 'sasew' 'hehea' '2s9df' 'kk22' '9rIaf2' 'DFDaj' '43adf' '9khieq' )

for ((i=0; i < ${#strings[@]}; i=i+2)); do
    tmpoutput=`echo -e ${strings[$i]}'\n'${strings[$i+1]} | ./hello`
    echo $tmpoutput | grep -q "${strings[$i]}"
    echo -n $?'@' >> output
    echo $tmpoutput | grep -q "${strings[$i+1]}"
    echo -n $?'@' >> output
    tmpoutput=""
done
echo "" >> output