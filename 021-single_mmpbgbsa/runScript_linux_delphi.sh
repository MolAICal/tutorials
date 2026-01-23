# Additional information
# 4. add water box
# molaical.exe -call run -c vmdargs -i -dispdev text -args solvate solvate complex_m.psf complex_m.pdb -t 5 -o complex_wb
# 5. add 0.15 nM Nacl
# molaical.exe -call run -c vmdargs -i -dispdev text -args autoionize autoionize -psf complex_wb.psf -pdb complex_wb.pdb -sc 0.15 -o complex_final

# 1. fix autopsf
molaical.exe -call run -c fixpsf

# 2. generate psf
molaical.exe -call run -c vmdargs -i -pdb $molargs1 -dispdev text -args autopsf autopsf -mol 0 -prefix protein
molaical.exe -call run -c vmdargs -i -pdb $molargs2 -dispdev text -args autopsf autopsf -mol 0 -top $molargs3 -prefix ligand

# 3. merge file
molaical.exe -call run -c merge -i -dispdev text -args -first ligand_formatted_autopsf.psf ligand_formatted_autopsf.pdb -second protein_formatted_autopsf.psf protein_formatted_autopsf.pdb -output complex_final

# 4. default to run 20 ps minimization and 40 ps MD simulation 
molaical.exe -call run -c runnamd -i -dispdev text -args -s complex_final.psf -c complex_final.pdb -nf md_configure.conf -output_prefix com_md

# 5. Cut last 10 steps for MM/GBSA calculation 
molaical.exe -call run -c catdcd -i -dispdev text -args -out result.dcd -first 51 -last 60 -stride 1 com_md.dcd

# 6. Calculate MM/GBSA
molaical.exe -call run -c mmpbgbsa -i -dispdev text -args -s complex_final.psf -c complex_final.pdb -t result.dcd -cs "segname,AP1,CO1" -rs "segname,AP1" -ls "segname,CO1" -pb 1 -ff $molargs3

# 7. delete file with command (in windows: del xxx, in linux: rm xxx)
rm *md.* *run.* *formatted* result.dcd *final.* *_md* *_wb*
