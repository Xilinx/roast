proc generate_dts args {
	set hwdesign [lindex $args 0]
	set repo [lindex $args 1]
	set dir [lindex $args 2]
	set board [lindex $args 3]
	puts "board $board"
	#setting workspace
	setws $dir
	if {[file isdirectory $dir]} {
		file delete -force $dir
	}
	repo -set "$repo"
	platform create -name hw0 -hw $hwdesign
	set proctype [hsi::get_cells -hier -filter {IP_TYPE==PROCESSOR}]
	set proc [lindex $proctype 0]
	domain create -name ${board}_dts -proc $proc -os device_tree
	# Supported boards:
	# kc705-full, kc705-lite, ac701-full, ac701-lite, kcu105, zc702, zc706, zedboard,
	# zcu102-reva, zcu102-revb, zcu102-rev1.0, zcu102-da10, zcu102-da7-es2, zcu102-da7-es2-rev1.1,
	# zc1751-dc1, zc1751-dc2, zcu100-reva, zcu100-revb, zcu100-revc, zcu104-reva, zcu104-revc, zcu106-reva.
	switch "$board" {
		"zcu100-reva" {
			bsp config periph_type_overrides "{BOARD zcu100-reva}"
			bsp config ${board}_dts stdin psu_uart_1
			bsp config ${board}_dts stdout psu_uart_1
		}
		"zcu100-revb" {
			bsp config periph_type_overrides "{BOARD zcu100-revb}"
			bsp config stdin psu_uart_1
			bsp config stdout psu_uart_1
		}
		"zcu100-revc" {
			bsp config periph_type_overrides "{BOARD zcu100-revc}"
			bsp config stdin psu_uart_1
			bsp config stdout psu_uart_1
		}
		"kcu105" {
			hsi::get_cells ddr4_sdram
			bsp config periph_type_overrides "{BOARD $board}"
		}
		default {
			bsp config periph_type_overrides "{BOARD $board}"
		}
	}
	platform generate

	if {[catch {exec ls {*}[glob -nocomplain $dir/hw0/${proc}/${board}_dts/bsp/*.dts*]} result] == 0} {
		puts "DTS Created:"
		set i 1
		foreach file ${result} {
			puts "\t $i.$file\n\r"
			set i [expr $i +1]
		}
		file mkdir $dir/${board}_dts
		set files [glob $dir/hw0/${proc}/${board}_dts/bsp/*]
		eval file copy $files $dir/${board}_dts
	} else {
		puts "No files created\n\r"
	}

}
set hwdesign [lindex $argv 0]
set dtg_repo [lindex $argv 1]
set output [lindex $argv 2]
set board [lindex $argv 3]
generate_dts "$hwdesign" "$dtg_repo" "$output" "$board"
