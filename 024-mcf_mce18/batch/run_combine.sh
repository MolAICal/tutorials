#!/bin/bash
cp /dev/null all.smi
for i in `ls -l | grep ".sdf" | awk '{print $9}'`
do
	# Above “.sdf” is a keyword. The below command is to remove the suffix.
	molaical.exe -tool tosmi -t sdf -q true -i $i > tmp.smi
	# Output last line.
        tail -n 1 tmp.smi >> all.smi
done
rm tmp.smi
