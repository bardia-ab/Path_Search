proc gen_bit {Proj_Dir Src_Dir Store_path folder_name N_Parallel} {
	set CUTs "$Src_Dir/$folder_name/CUTs.vhd"
	set constraint "$Src_Dir/$folder_name/physical_constraints.xdc"
	set stats "$Src_Dir/$folder_name/stats.txt"
	set prev_CUTs [get_files *CUTs*]
	set prev_constraint [get_files *physical_constraints*]
	set ProjName [lindex [split "$Proj_Dir" /] end]
	set bd_file "$Proj_Dir/$ProjName\.srcs/sources_1/bd/design_1/design_1.bd"
	set bitstream_file "$Store_path/Bitstreams/$folder_name\.bit"
	set DCP_file "$Store_path/DCPs/$folder_name\.dcp"
	#set logfile "$Proj_Dir/$ProjName\.runs/impl_1/runme.log"
	#set logfile_dest "$Store_path/Logs/$folder_name\.log"

	delete_runs synth_1

	if {[llength $prev_CUTs] > 0} {
		remove_files  -fileset constrs_1 "$prev_CUTs"
	}
	add_files -norecurse "$CUTs"
	set_property file_type {VHDL 2008} [get_files $CUTs]
	if {[llength $prev_constraint] > 0} {
		remove_files  -fileset constrs_1 "$prev_constraint"
	}
	add_files -fileset constrs_1 -norecurse "$constraint"
	set_property used_in_synthesis false [get_files  "$constraint"]
	update_module_reference design_1_top_0_0
	update_compile_order -fileset sources_1
	#upgrade_ip [get_ips]
	open_bd_design "$bd_file"
	startgroup
	lassign [get_segmentation "$stats"] N_Segments N_Partial
	set_property -dict [list CONFIG.g_N_Parallel $N_Parallel CONFIG.g_N_Segments $N_Segments CONFIG.g_N_Partial $N_Partial] [get_bd_cells top_0]
	endgroup
	save_bd_design
	validate_bd_design
	catch {launch_runs impl_1 -jobs 12}
	catch {wait_on_run impl_1}
	#file copy $logfile $logfile_dest
	set_param xicom.use_bitstream_version_check false
	open_run impl_1
	set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]
	write_bitstream -force $bitstream_file
	write_checkpoint -force $DCP_file

}

proc get_segmentation {stats} {
	set file [open "$stats" r]
	set lines [read "$file"]
	regexp {(\d+).* (\d+)} $lines match N_Segments N_Partial
	
	return [list $N_Segments $N_Partial]
}

proc wsplit {string sep} {
    set first [string first $sep $string]
    if {$first == -1} {
        return [list $string]
    } else {
        set l [string length $sep]
        set left [string range $string 0 [expr {$first-1}]]
        set right [string range $string [expr {$first+$l}] end]
        return [concat [list $left] [wsplit $right $sep]]
    }
}


#set Src_Dir /home/bardia/Desktop/bardia/Timing_Characterization/Data/Vivado_Sources
#set Proj_Dir /home/bardia/Desktop/bardia/FPGA_Projects/CPS_Parallel_ZCU9
#set Store_path /home/bardia/Desktop/bardia/Timing_Characterization/Data
set Src_Dir [lindex $argv 0]
set Proj_Dir [lindex $argv 1]
set Store_path [lindex $argv 2]
set ProjName [lindex [split "$Proj_Dir" /] end]
set logfile "$Proj_Dir/$ProjName\.runs/impl_1/runme.log"

open_project "$Proj_Dir/$ProjName\.xpr"
set_msg_config -severity {CRITICAL WARNING} -new_severity ERROR
if {[lindex $argv 6] == {None}} {
	for {set i [lindex $argv 3]} {$i < [lindex $argv 4]} {incr i} {
		set folder_name "TC$i"
		catch {gen_bit $Proj_Dir $Src_Dir $Store_path $folder_name [lindex $argv 5]}
		set logfile_dest "$Store_path/Logs/$folder_name\.log"
		catch {file copy $logfile $logfile_dest}
	}
} elseif {[lindex $argv 6] == {custom}} {
    set TCs [glob -dir $Src_Dir *]
    set TCs [lsort $TCs]
    foreach TC $TCs {
		set folder_name [lindex [wsplit $TC "/"] end]
		catch {gen_bit $Proj_Dir $Src_Dir $Store_path $folder_name [lindex $argv 5]}
		set logfile_dest "$Store_path/Logs/$folder_name\.log"
		catch {file copy $logfile $logfile_dest}
	}
} else {
	set TCs_even_odd [glob -dir $Src_Dir *even]
	lappend TCs_even_odd {*}[glob -dir $Src_Dir *odd]
	set TCs_even_odd [lsort $TCs_even_odd]
	foreach TC_even_odd $TCs_even_odd {
		set folder_name [lindex [wsplit $TC_even_odd "/"] end]
		catch {gen_bit $Proj_Dir $Src_Dir $Store_path $folder_name [lindex $argv 5]}
		set logfile_dest "$Store_path/Logs/$folder_name\.log"
		catch {file copy $logfile $logfile_dest}
	}
}

