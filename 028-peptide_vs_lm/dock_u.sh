# Generate swarms
# 1.1 no memebrane
# molaical.exe -call run -c ldock -i lightdock3_setup.py $molargs1 $molargs2 --noxt --noh --now -rst $molargs3
# 1.2. memebrane
molaical.exe -call run -c ldock -i lightdock3_setup.py $molargs1 $molargs2 -membrane --noxt --noh --now -rst $molargs3

# 2. Run simulations
molaical.exe -call run -c ldock -i lightdock3.py setup.json 100 -s fastdfire -c $molargs6 -min

# 3. Generate models, Clustering, Rank, and filter
molaical.exe -call run -c sfile -i lrank.sh 1::=$molargs1 2::=$molargs2 3::=$molargs4 4::=$molargs5 5::=$molargs6 6::=$molargs3

# 3. Generate models, Clustering, Rank, and filter. Default debug mode is 1 which does not delete the temporary files. 
# Setting 16::=0 will delete the temporary files if users make sure progress is corrected
# molaical.exe -call run -c sfile -i lrank.sh 1::=$molargs1 2::=$molargs2 3::=$molargs4 4::=$molargs5 5::=$molargs6 6::=$molargs3 16::=0

# 4. Get the top candidate from the above results
molaical.exe -call run -c sfile -i mrank.py -ft 1

# 5. MM/GBSA
molaical.exe -call run -c sfile -i mmgbpbsa_batch.sh 1::=$molargs4 2::=$molargs5 9::=$molargs7

# 6. Get the top candidate from MM/GBSA results 
molaical.exe -call run -c sfile -i mrank.py -t 1
