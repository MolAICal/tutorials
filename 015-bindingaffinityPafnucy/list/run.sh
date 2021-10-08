#!/bin/bash

i=0
cat list.txt | while read line
do
	echo $line
	~/bai/soft/moaicalv11/molaical.exe -model pafnucy -l $line -p pocket.mol2 -o $line'.csv'
	let i+=1
done



