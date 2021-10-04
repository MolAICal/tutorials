set outfile [open moldconf.txt w]
set sel [atomselect top all]

puts $outfile "out = mold.pdbqt"
puts $outfile "cpu = 10"
puts $outfile "energy_range = 10"
set center [measure center $sel]
set cx [lindex $center 0]
set cy [lindex $center 1]
set cz [lindex $center 2]
puts $outfile "center_x = $cx"
puts $outfile "center_y = $cy"
puts $outfile "center_z = $cz"

set minmax [measure minmax $sel]
set vec [vecsub [lindex $minmax 1] [lindex $minmax 0]]
set vecX [vecadd [lindex $vec 0] 15]
set vecY [vecadd [lindex $vec 1] 15]
set vecZ [vecadd [lindex $vec 2] 15]
puts $outfile "size_x = $vecX"
puts $outfile "size_y = $vecY"
puts $outfile "size_z = $vecZ"
puts $outfile "num_modes = 1"
close $outfile
exit

