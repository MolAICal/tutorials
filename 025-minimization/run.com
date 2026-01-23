open GCGRH_fix.pdb
open GCGRH.pdb
open lig_10.mol2
combine #1,2 modelId 3
delete #1,2
select #0 za<0.01
delete #0
addh
addcharge all method gas
minimize freeze selected prep false nsteps 10 stepsize 0.02 cgsteps 2 cgstepsize 0.02 interval 1 nogui true
~select
select #3:<0>
write selected format mol2 relative 3 #3 out_1.mol2
select invert selected
write selected format pdb relative 3 #3 out_2.pdb
stop